# Arquitetura proposta (produção) - SaaS fiscal focado em SEFAZ GO

## 1) Objetivo

Automatizar consulta e download de documentos fiscais (DANFE/XML) para múltiplos CNPJs clientes, cobrindo **NF-e (55)** e **NFC-e (65)** de entrada/saída, com foco operacional em escala (de empresas pequenas até operações com alto volume).

## 2) Componentes

- **Painel SaaS Web**: cadastro de empresas, certificados, agenda, regras de consulta, monitoramento de jobs.
- **API Backend**: autenticação, gestão de tenants, enfileiramento, auditoria e disponibilização de XMLs/metadados.
- **Orquestrador de Coleta**:
  - Conector API oficial (prioritário quando disponível).
  - Conector portal (somente onde permitido e tecnicamente viável).
- **Fila de processamento**: jobs por empresa/competência para controlar rate-limit e paralelismo.
- **Armazenamento de XML**: object storage com versionamento e trilha de auditoria.
- **Banco transacional**: empresas, jobs, documentos, falhas, checkpoints.

## 3) Modelo multi-empresa

- Cada empresa possui:
  - CNPJ
  - UF alvo (GO)
  - tipo de certificado (A1/A3)
  - estratégia de conexão
  - janela de consulta
  - políticas de retry
- Jobs segregados por tenant para evitar que cliente de alto volume bloqueie os demais.

## 4) Estratégia para alto volume (ex.: supermercado com 50k XML modelo 65)

- Coleta incremental por janelas curtas (ex.: hora a hora) + reconciliação diária.
- Paginação/checkpoint por NSU/chave/data conforme API/fonte disponível.
- Download concorrente controlado por CNPJ e por endpoint.
- Deduplicação por chave de acesso (44 dígitos).
- Reprocessamento idempotente.

## 5) Segurança e compliance

- Segredos/certificados em cofre (KMS/Secret Manager).
- Criptografia em trânsito e em repouso.
- Auditoria completa por requisição e documento.
- Respeito a termos de uso e limites dos órgãos fiscais.

## 6) Observabilidade

- Métricas: throughput de docs/min, latência por job, taxa de erro por empresa.
- Alertas: falha de autenticação, captcha recorrente, backlog acima do limite.
- Dashboard operacional por contador/carteira de clientes.

