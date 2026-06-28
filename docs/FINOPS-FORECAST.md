# FinOps — Forecast de Custos

## Tagging Strategy

Todos os recursos AWS recebem as seguintes tags via `default_tags` no Terraform:

```hcl
default_tags {
  tags = {
    Project     = "SolidaryTech"
    Environment = "Production" | "DR"
    CostCenter  = "NGO-Core"
    ManagedBy   = "Terraform"
    Team        = "DevOps"
  }
}
```

Isso permite filtrar custos por `CostCenter` no AWS Cost Explorer.

---

## Estimativa Mensal (us-east-1)

| Serviço | Configuração | Custo Est. (USD/mês) |
|---------|-------------|----------------------|
| EKS Control Plane | 1 cluster | $73 |
| EC2 Nodes | 2× t3.medium (on-demand) | $61 |
| RDS PostgreSQL | db.t3.micro Multi-AZ | $29 |
| DynamoDB | On-demand (baixo volume) | $5 |
| SQS | < 1M req/mês | $0.40 |
| ECR | 3 repos, ~1GB | $0.30 |
| ALB | 1 load balancer | $18 |
| NAT Gateway | 1 NAT | $32 |
| S3 (velero + tfstate) | < 10GB | $0.50 |
| CloudWatch Logs | ~5GB/mês | $2.50 |
| **Total Produção** | | **~$222/mês** |
| DR (us-west-2, idle) | EKS + RDS apenas | ~$110/mês |
| **Total Geral** | | **~$332/mês** |

---

## Otimizações Implementadas

| Otimização | Impacto |
|-----------|---------|
| Spot Instances para node group (futura melhoria) | -60% EC2 |
| NAT Gateway single AZ no DR | -$32/mês |
| ECR lifecycle policy (keep 10 images) | Minimiza storage |
| RDS `deletion_protection=false` no DR | Evita custos acidentais |
| DynamoDB on-demand | Paga apenas pelo uso |

---

## Alertas de Custo

Configurar no AWS Budgets:
- Alerta 80% do orçamento mensal → notificação por e-mail
- Alerta 100% → PagerDuty P2

```bash
aws budgets create-budget \
  --account-id $AWS_ACCOUNT_ID \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

---

## Recomendações Futuras

1. **Savings Plans** para EKS nodes (após 3 meses de baseline)
2. **Karpenter** no lugar do managed node group → melhor bin-packing
3. **S3 Intelligent-Tiering** para bucket Velero > 90 dias
