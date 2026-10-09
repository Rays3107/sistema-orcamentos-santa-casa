# Integração — Orçamento Santa Casa

Projeto separado para integrar o site de orçamento hospitalar ao banco SQLite `BDORCAMENTO.db`.

## Estrutura

- `frontend/index.html` — cópia de trabalho do site atual.
- `backend/app.py` — API Flask inicial para acesso ao SQLite.
- `backend/requirements.txt` — dependência do backend.
- `database/BDORCAMENTO.db` — banco de trabalho entregue.
- `database/schema.sql` — estrutura do banco.
- `backup_original/` — cópias intocadas dos arquivos recebidos.
- `docs/` — documentação e decisões da integração.

## Situação encontrada

O site atual é um HTML único e grava o preenchimento localmente em `localStorage`.
O banco enviado é SQLite e contém as tabelas:

- `orcamentos`
- `orcamento_itens`
- `exames`
- `opme`
- `usuarios`
- `historico_orcamento`

O banco entregue está sem registros.

## Próximo passo técnico

Migrar o salvamento do formulário do `localStorage` para os endpoints `/api/orcamentos` e, depois,
implementar carregamento/edição, itens, exames, OPME, usuários e histórico.

## Execução local

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Depois abrir `http://127.0.0.1:5000/`.

> O arquivo em `backup_original` não deve ser alterado. Qualquer manutenção deve ser feita nas cópias de trabalho.
