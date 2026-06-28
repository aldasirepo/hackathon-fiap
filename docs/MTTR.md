# MTTR — Mean Time to Recovery

## Definições

| Métrica | Fórmula | Meta |
|---------|---------|------|
| MTTD | Tempo detecção do incidente | < 5 min |
| MTTR | Tempo total até resolução | < 30 min (P1) |
| MTBF | Tempo médio entre falhas | > 720h/mês |
| Change Failure Rate | % deploys que causam incidentes | < 5% |

---

## Estratégias para Reduzir MTTR

### 1. Observabilidade (MTTD → 0)
- Prometheus coleta métricas a cada 15s
- AlertManager dispara em < 1 min após threshold
- Grafana Tempo: trace completo de request cross-service
- Loki: logs centralizados com correlação por trace_id

### 2. Rollback Automático (MTTR rápido)
```yaml
# ArgoCD selfHeal reverte automaticamente
syncPolicy:
  automated:
    selfHeal: true
    prune: true
```

### 3. Deployment Strategies
- `RollingUpdate` nos deployments: `maxUnavailable: 0, maxSurge: 1`
- Sempre manter a versão anterior disponível por pelo menos 1 hora
- Health checks obrigatórios antes de remover pods antigos

### 4. Chaos Engineering (Gameday)
Trimestral:
- Matar pods aleatoriamente: `kubectl delete pod -l app=ngo-service -n solidarytech`
- Simular falha de AZ via Security Group
- Testar failover DR completo

---

## Cálculo do MTTR Meta

```
Meta SLO: 99.5% disponibilidade/mês
Total minutos: 43.200

Downtime permitido: 43.200 × 0.005 = 216 min/mês

Assumindo max 3 incidentes P1/mês:
MTTR meta = 216 / 3 = 72 min por incidente

Meta agressiva: MTTR < 30 min (com automação)
```

---

## Rastreamento (a implementar)

Registrar em cada post-mortem:
- Timestamp detecção (MTTD)
- Timestamp resolução (MTTR)
- Root cause category: Deploy / Config / Infra / Dependência externa
- Ação preventiva aplicada

Dashboard Grafana: painel `MTTR histórico` alimentado por labels dos alertas.
