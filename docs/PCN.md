# PCN — Plano de Continuidade de Negócios

## Estratégia de DR: Warm Standby

| Região | Função | RTO | RPO |
|--------|--------|-----|-----|
| us-east-1 | Produção (ativa) | — | — |
| us-west-2 | DR (warm standby) | 30 min | 15 min |

---

## Componentes Replicados

| Componente | Mecanismo | Frequência |
|-----------|-----------|------------|
| RDS PostgreSQL | Snapshot + restore cross-region | A cada 6h (automático AWS) |
| DynamoDB | Global Tables (opcional) / Backup on-demand | Diário |
| Imagens ECR | Replicação ECR cross-region | Push automático |
| Backups K8s | Velero → S3 | Diário às 02:00 UTC |
| IaC | Terraform environment/dr | Sob demanda |

---

## Procedimento de Failover

### 1. Detecção (0–5 min)
- AlertManager dispara `RegionDown` → PagerDuty → on-call
- Verificar CloudWatch: EKS, RDS, ALB health

### 2. Ativação do DR (5–20 min)
```bash
# 1. Restaurar RDS snapshot mais recente em us-west-2
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier solidarytech-dr \
  --db-snapshot-identifier <latest-snapshot> \
  --region us-west-2

# 2. Aplicar terraform no ambiente DR
cd terraform-hackathon/environments/dr
terraform init
terraform apply -var="rds_password=$TF_VAR_rds_password"

# 3. Restaurar workloads via Velero
velero restore create --from-backup daily-backup-$(date +%Y%m%d)
```

### 3. Atualizar DNS (20–30 min)
- Route53: Failover routing policy já configurado
- Health check aponta para ALB de cada região
- TTL: 60s para failover rápido

### 4. Validação
```bash
kubectl get pods -n solidarytech
curl https://api-dr.solidarytech.example.com/ngos/health
curl https://api-dr.solidarytech.example.com/donations/health
curl https://api-dr.solidarytech.example.com/volunteers/health
```

### 5. Pós-Incidente
- Documentar no ITSM (ITSM-INCIDENT-FLOW.md)
- Calcular impacto no Error Budget
- Post-mortem em até 48h

---

## Testes de DR

| Frequência | Tipo | Responsável |
|-----------|------|-------------|
| Trimestral | Failover completo (gameday) | DevOps Lead |
| Mensal | Velero restore test | DevOps |
| Semanal | Validação de snapshots | Automatizado |
