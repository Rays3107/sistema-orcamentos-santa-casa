# Mapa inicial da integração

## Banco

Banco: SQLite 3
Arquivo de trabalho: `database/BDORCAMENTO.db`

### Relacionamentos principais

`orcamentos.id`
→ `orcamento_itens.orcamento_id`
→ `exames.orcamento_id`
→ `opme.orcamento_id`
→ `historico_orcamento.orcamento_id`

`usuarios.id`
→ `orcamentos.criado_por`
→ `historico_orcamento.usuario_id`

## Site atual

O HTML entregue possui banco SQLite embutido em Base64 para download, mas o preenchimento atual
é salvo no navegador via `localStorage`. Portanto, para uma integração real com o SQLite,
o navegador deverá conversar com um backend/API.

## Regra de manutenção

1. Nunca editar `backup_original`.
2. Fazer alterações no `frontend/` e `backend/`.
3. Testar contra uma cópia do banco antes de usar o banco oficial.
4. Registrar mudanças em `docs/CHANGELOG.md`.
