# ITSM — Fluxo de Incidentes (AIOps)

## Classificação de Severidade

| Severidade | Critério | SLA Resposta | SLA Resolução |
|-----------|---------|-------------|--------------|
| P1 — Crítico | Plataforma fora / perda de dados | 5 min | 1h |
| P2 — Alto | Serviço degradado >10% usuários | 15 min | 4h |
| P3 — Médio | Funcionalidade não-crítica afetada | 1h | 8h |
| P4 — Baixo | Cosmético / melhoria | 24h | Sprint |

---

## Fluxo de Detecção → Resolução

```
Prometheus (regras SLI)
        │
        ▼
  AlertManager
   ┌────┴────┐
   │         │
PagerDuty  Slack #alerts
   │
   ▼
On-Call Engineer (5 min)
   │
   ├─ P1/P2 → Abrir incidente no sistema de tickets
   │           Notificar time via #incident-war-room
   │
   ▼
Diagnóstico (15 min)
   │
   ├─ Verificar Grafana dashboards (SRE Dashboard)
   ├─ Checar Grafana Loki (logs agregados)
   ├─ Checar Grafana Tempo (traces distribuídos)
   └─ kubectl describe / logs
   │
   ▼
Mitigação
   │
   ├─ Rollback ArgoCD (auto-sync reverterá se selfHeal=true)
   │   argocd app rollback solidarytech-app
   │
   ├─ Scale up manual
   │   kubectl scale deploy/ngo-service --replicas=5 -n solidarytech
   │
   └─ Failover para DR (ver PCN.md)
   │
   ▼
Resolução + Post-Mortem (48h)
```

---

## Alertas Configurados (AlertManager)

| Alerta | Condição | Severidade |
|--------|---------|-----------|
| `HighErrorRate` | error_rate > 1% por 5min | critical |
| `HighLatency` | p99 > 500ms por 10min | warning |
| `PodCrashLooping` | restart_count > 5 em 15min | critical |
| `NodeNotReady` | node status != Ready | critical |
| `ErrorBudgetBurn` | burn_rate > 14.4× em 1h | critical |

---

## Runbooks

### RDB Connection Exhaustion
```bash
# Ver conexões ativas
kubectl exec -it deploy/ngo-service -n solidarytech -- \
  psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Forçar pool reconnect
kubectl rollout restart deploy/ngo-service -n solidarytech
```

### SQS DLQ com mensagens
```bash
# Ver quantidade no DLQ
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/ACCOUNT/solidarytech-donations-dlq \
  --attribute-names ApproximateNumberOfMessages

# Reprocessar (mover DLQ → fila principal)
# Usar AWS Console > SQS > Start DLQ redrive
```

---

## AIOps Integration

O Grafana Alerting está integrado com:
- **PagerDuty**: Incidents P1/P2 → escalation automático
- **Slack #alerts**: Todos os alertas
- **Slack #sre-oncall**: Apenas P1/P2

Futura integração com AWS DevOps Guru para anomaly detection automático.
