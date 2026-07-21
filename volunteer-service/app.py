import os
import sys
import uuid
import time
import logging
import boto3
from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv

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
        method=request.method, endpoint=request.path, service='volunteer-service'
    ).observe(latency)
    REQUEST_COUNT.labels(
        method=request.method, endpoint=request.path,
        status=response.status_code, service='volunteer-service'
    ).inc()
    return response

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

# OpenTelemetry tracing
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://tempo.monitoring.svc.cluster.local:4317")
resource = Resource.create({"service.name": "volunteer-service", "service.version": "1.0.0"})
provider = TracerProvider(resource=resource)
try:
    exporter = OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
except Exception as e:
    log.warning(f"OTel exporter não inicializado: {e}")
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("volunteer-service")

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DYNAMODB_TABLE = os.getenv("AWS_DYNAMODB_TABLE")

if not DYNAMODB_TABLE:
    log.critical("Erro: AWS_DYNAMODB_TABLE não definida.")
    sys.exit(1)

try:
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    table = dynamodb.Table(DYNAMODB_TABLE)
    log.info(f"Conectado à tabela DynamoDB: {DYNAMODB_TABLE}")
except Exception as e:
    log.critical(f"Falha ao conectar no DynamoDB: {e}")
    sys.exit(1)

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "volunteer-service"})

@app.route('/volunteers', methods=['POST'])
def register_volunteer():
    with tracer.start_as_current_span("register_volunteer"):
        data = request.get_json()
        if not data or not all(k in data for k in ('name', 'email', 'ngo_id')):
            return jsonify({"error": "Campos obrigatórios ausentes"}), 400

        volunteer_id = str(uuid.uuid4())
        item = {
            'volunteer_id': volunteer_id,
            'name': data['name'],
            'email': data['email'],
            'ngo_id': int(data['ngo_id']),
            'registered_at': str(int(time.time()))
        }

        try:
            table.put_item(Item=item)
            return jsonify(item), 201
        except Exception as e:
            log.error(f"Erro ao salvar voluntário no DynamoDB: {e}")
            return jsonify({"error": "Erro interno ao processar dados"}), 500

@app.route('/volunteers/<int:ngo_id>', methods=['GET'])
def get_volunteers_by_ngo(ngo_id):
    with tracer.start_as_current_span("get_volunteers_by_ngo"):
        try:
            response = table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('ngo_id').eq(ngo_id)
            )
            return jsonify(response.get('Items', [])), 200
        except Exception as e:
            log.error(f"Erro ao buscar dados no DynamoDB: {e}")
            return jsonify({"error": "Erro interno"}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8083))
    app.run(host='0.0.0.0', port=port)
