# Changelog — hackathon-fiap

## [2.0.0] — 2026-06-27

### Added
- `docs/SLI-SLO-SLA.md` — definição de SLIs, SLOs, SLAs e error budget
- `docs/PCN.md` — Plano de Continuidade de Negócios (DR Warm Standby)
- `docs/FINOPS-FORECAST.md` — estimativa de custos e tagging strategy
- `docs/ITSM-INCIDENT-FLOW.md` — fluxo de incidentes e runbooks
- `docs/MTTR.md` — métricas e estratégias para redução do MTTR
- `.gitignore` — exclui __pycache__, *.exe, .terraform, IDE files

### Changed
- `.github/workflows/ngo-service.yml` — usa `role-to-assume` (sem keys), kustomize edit set image
- `.github/workflows/donation-service.yml` — idem
- `.github/workflows/volunteer-service.yml` — idem
- `k8s/overlays/production/kustomization.yaml` — images block sem ACCOUNT_ID hardcoded

### Removed
- `argocd/application.yaml` — duplicata de CD/apps/root-app.yaml (deletar via PowerShell)
- `donation-service/donation-service.exe` — binário acidental (deletar via PowerShell)
- `__pycache__/` — diretórios Python cache (deletar via PowerShell)

### Security
- CI/CD usa OIDC `role-to-assume` em vez de access keys
- ACCOUNT_ID nunca hardcoded — injetado via `${{ steps.ecr-login.outputs.registry }}`
