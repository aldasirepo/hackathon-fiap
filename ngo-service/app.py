import os
import sys
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv
import logging

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total', 'Total HTTP requests',
    ['method', 'endpoint', 'status', 'service']
)
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds', 'HTTP request latency',
    ['method', 'endpoint', 'service']
)

@app.before_request
def before_request():
    request._start_time = time.time()

@app.after_request
def after_request(response):
    latency = time.time() - getattr(request, '_start_time', time.time())
    REQUEST_LATENCY.labels(
        method=request.method, endpoint=request.path, service='ngo-service'
    ).observe(latency)
    REQUEST_COUNT.labels(
        method=request.method, endpoint=request.path,
        status=response.status_code, service='ngo-service'
    ).inc()
    return response

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

# OpenTelemetry tracing
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://tempo.monitoring.svc.cluster.local:4317")
resource = Resource.create({"service.name": "ngo-service", "service.version": "1.0.0"})
provider = TracerProvider(resource=resource)
try:
    exporter = OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
except Exception as e:
    log.warning(f"OTel exporter não inicializado: {e}")
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("ngo-service")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    log.critical("Erro: DATABASE_URL não definida.")
    sys.exit(1)

try:
    pool = SimpleConnectionPool(1, 10, dsn=DATABASE_URL)
    log.info("Pool de conexões com o PostgreSQL (ngo-service) inicializado.")
except Exception as e:
    log.critical(f"Erro ao conectar ao PostgreSQL: {e}")
    sys.exit(1)

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "ngo-service"})

@app.route('/ngos', methods=['POST'])
def create_ngo():
    with tracer.start_as_current_span("create_ngo"):
        data = request.get_json()
        if not data or not all(k in data for k in ('name', 'email', 'cause', 'city')):
            return jsonify({"error": "Campos obrigatórios ausentes"}), 400

        conn = pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "INSERT INTO ngos (name, email, cause, city) VALUES (%s, %s, %s, %s) RETURNING *",
                    (data['name'], data['email'], data['cause'], data['city'])
                )
                new_ngo = cur.fetchone()
                conn.commit()
                return jsonify(new_ngo), 201
        except psycopg2.IntegrityError:
            conn.rollback()
            return jsonify({"error": "E-mail já cadastrado"}), 409
        except Exception as e:
            conn.rollback()
            log.error(f"Erro ao criar ONG: {e}")
            return jsonify({"error": "Erro interno"}), 500
        finally:
            pool.putconn(conn)

@app.route('/ngos', methods=['GET'])
def get_ngos():
    with tracer.start_as_current_span("get_ngos"):
        conn = pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM ngos ORDER BY id DESC")
                return jsonify(cur.fetchall()), 200
        except Exception as e:
            log.error(f"Erro ao buscar ONGs: {e}")
            return jsonify({"error": "Erro interno"}), 500
        finally:
            pool.putconn(conn)

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8081))
    app.run(host='0.0.0.0', port=port)
