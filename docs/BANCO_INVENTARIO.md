# Inventário do banco
- Arquivo: `BDORCAMENTO.db`
- Tabelas: 7

## exames
- Registros: 0
- Colunas: id, orcamento_id, descricao, quantidade, valor_unitario, valor_total, ordem

## historico_orcamento
- Registros: 0
- Colunas: id, orcamento_id, usuario_id, acao, descricao, criado_em

## opme
- Registros: 0
- Colunas: id, orcamento_id, descricao, quantidade, unidade, fornecedor, observacao, valor, ordem

## orcamento_itens
- Registros: 0
- Colunas: id, orcamento_id, acomodacao, descricao, quantidade, unidade, valor_unitario, valor_total, ordem

## orcamentos
- Registros: 0
- Colunas: id, numero, tipo, paciente_nome, paciente_contato, prontuario, medico_responsavel, procedimento, data_orcamento, validade, forma_pagamento, observacao_pagamento, itens_inclusos, itens_exclusos, total, status, criado_por, criado_em, atualizado_em

## sqlite_sequence
- Registros: 0
- Colunas: name, seq

## usuarios
- Registros: 0
- Colunas: id, nome, login, senha_hash, ativo, criado_em
