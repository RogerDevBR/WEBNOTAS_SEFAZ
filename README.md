# WEBNOTAS SEFAZ GO (Mockup SaaS)

Mockup funcional de um SaaS para:

- Cadastrar empresas/clientes (multi-tenant simples).
- Configurar estratégia de consulta (API oficial ou portal/raspagem).
- Executar sincronização de documentos fiscais (NF-e modelo 55 e NFC-e modelo 65, entrada/saída).
- Simular download em lote para clientes de alta movimentação.

> **Importante:** este projeto é um **mockup executável**. Ele não burla CAPTCHA nem acessa ambiente real da SEFAZ-GO neste momento. O conector atual é um adaptador `mock`, preparado para ser trocado por conectores reais.

## Como executar

```bash
python3 app.py
```

Acesse: `http://localhost:8000`

## Fluxo de demonstração (1 cliente)

1. Abra a interface web.
2. Cadastre uma empresa (nome e CNPJ).
3. Clique em **Sincronizar agora** para essa empresa.
4. O sistema cria um job, processa e gera documentos mock (55/65, entrada/saída).
5. Clique em **Ver docs** para inspecionar os registros e o caminho do arquivo XML baixado.

## Estrutura

- `app.py`: servidor HTTP + API REST + persistência SQLite + motor de sync mock.
- `static/`: frontend mockup (dashboard SaaS).
- `tests/test_sync.py`: teste automatizado do fluxo principal.
- `docs/ARCHITECTURE.md`: arquitetura alvo para produção (SEFAZ GO).
- `docs/INTEGRATION_NOTES.md`: estratégias reais de integração, riscos legais/técnicos e próximos passos.

## Testes

```bash
python3 -m unittest -v
```

