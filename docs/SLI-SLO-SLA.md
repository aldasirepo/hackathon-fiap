# SLI / SLO / SLA — SolidaryTech

## Definições

| Sigla | Conceito |
|-------|----------|
| SLI   | Métrica real observada (ex: taxa de erros) |
| SLO   | Meta interna de confiabilidade |
| SLA   | Contrato externo com penalidades |

---

## SLOs por Serviço

### ngo-service (API REST - Python)

| SLI | Métrica | SLO | Janela |
|-----|---------|-----|--------|
| Disponibilidade | `(requests_total - errors_total) / requests_total` | ≥ 99.5% | 30 dias |
| Latência p99 | `histogram_quantile(0.99, http_request_duration_seconds_bucket)` | ≤ 500ms | 30 dias |
| Taxa de erro | `rate(http_requests_total{status=~"5.."}[5m])` | < 0.1% | 30 dias |

### donation-service (API REST - Go)

| SLI | Métrica | SLO | Janela |
|-----|---------|-----|--------|
| Disponibilidade | Mesmo cálculo | ≥ 99.5% | 30 dias |
| Latência p99 | | ≤ 300ms | 30 dias |
| Taxa de erro | | < 0.1% | 30 dias |
| Processamento SQS | `sqs_messages_processed_total / sqs_messages_received_total` | ≥ 99.9% | 30 dias |

### volunteer-service (API REST - Python)

| SLI | Métrica | SLO | Janela |
|-----|---------|-----|--------|
| Disponibilidade | | ≥ 99.0% | 30 dias |
| Latência p99 | | ≤ 500ms | 30 dias |
| Taxa de erro | | < 0.5% | 30 dias |

---

## Error Budget

```
Error Budget (mensal) = (1 - SLO) × total_minutos
                      = (1 - 0.995) × 43200
                      = 216 minutos/mês
```

Quando o Error Budget atingir 50%, congelar deploys não-críticos.  
Quando atingir 0%, parar deploys e focar em confiabilidade.

---

## SLA (Externo)

| Tier | Disponibilidade | Crédito |
|------|----------------|---------|
| Standard | ≥ 99.0% | 10% da fatura mensal |
| Premium  | ≥ 99.5% | 25% da fatura mensal |

---

## Recording Rules (Prometheus)

```yaml
# observability/prometheus/rules.yaml
- record: job:request_error_rate:ratio_rate5m
  expr: |
    sum(rate(http_requests_total{status=~"5.."}[5m])) by (job)
    /
    sum(rate(http_requests_total[5m])) by (job)

- record: job:request_latency_p99:histogram_quantile
  expr: |
    histogram_quantile(0.99,
      sum(rate(http_request_duration_seconds_bucket[5m])) by (job, le)
    )
```
