# Notas de integração real com SEFAZ GO

## Premissas práticas

1. **Priorizar APIs oficiais/documentadas** da SEFAZ e integrações autorizadas.
2. **Evitar abordagem de raspagem com CAPTCHA/iframe** como caminho principal, pois é frágil e pode violar termos.
3. Tratar portal com CAPTCHA apenas como contingência manual assistida (quando juridicamente permitido).

## Caminho recomendado de implementação real

- Levantar canais oficiais disponíveis para consulta/distribuição de DF-e para os modelos 55 e 65 em GO.
- Definir autenticação por certificado digital (A1/A3) por empresa.
- Implementar cliente de integração resiliente:
  - timeout, retry com backoff, circuit breaker;
  - controle de taxa por CNPJ.
- Persistir checkpoints por empresa para coleta incremental.

## Sobre ferramentas tipo Qive

Soluções como Qive operam com arquitetura robusta de integração, filas, observabilidade, compliance e tratamento massivo de exceções. Este mockup já separa os blocos principais para você evoluir nessa direção sem depender de processo manual.

## Riscos da raspagem

- CAPTCHA recorrente inviabiliza automação contínua.
- Mudança de HTML/iframe quebra robôs frequentemente.
- Exposição jurídica/operacional se burlar mecanismos anti-bot.

## Próximos passos técnicos

1. Trocar `mock_provider` por `sefaz_go_provider`.
2. Implementar fluxo de certificado e assinatura quando exigido.
3. Adicionar fila (Redis/RQ ou Celery) para produção.
4. Adicionar autenticação de usuários e isolamento por escritório/cliente.
5. Expandir exportações (ZIP mensal, integração contábil, webhook).

