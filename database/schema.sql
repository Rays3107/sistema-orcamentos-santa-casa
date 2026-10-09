CREATE INDEX idx_exames_orcamento
ON exames(orcamento_id)

CREATE INDEX idx_historico_orcamento
ON historico_orcamento(orcamento_id)

CREATE INDEX idx_opme_orcamento
ON opme(orcamento_id)

CREATE INDEX idx_orcamento_itens_orcamento
ON orcamento_itens(orcamento_id)

CREATE INDEX idx_orcamentos_data
ON orcamentos(data_orcamento)

CREATE INDEX idx_orcamentos_numero
ON orcamentos(numero)

CREATE INDEX idx_orcamentos_paciente
ON orcamentos(paciente_nome)

CREATE INDEX idx_orcamentos_prontuario
ON orcamentos(prontuario)

CREATE INDEX idx_orcamentos_status
ON orcamentos(status)

CREATE INDEX idx_orcamentos_tipo
ON orcamentos(tipo)

CREATE TABLE exames (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    orcamento_id INTEGER NOT NULL,

    descricao TEXT NOT NULL,

    quantidade REAL NOT NULL DEFAULT 1
        CHECK (quantidade > 0),

    valor_unitario REAL NOT NULL DEFAULT 0
        CHECK (valor_unitario >= 0),

    valor_total REAL NOT NULL DEFAULT 0
        CHECK (valor_total >= 0),

    ordem INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (orcamento_id)
        REFERENCES orcamentos(id)
        ON DELETE CASCADE
)

CREATE TABLE historico_orcamento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    orcamento_id INTEGER NOT NULL,

    usuario_id INTEGER,

    acao TEXT NOT NULL,

    descricao TEXT,

    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (orcamento_id)
        REFERENCES orcamentos(id)
        ON DELETE CASCADE,

    FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
)

CREATE TABLE opme (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    orcamento_id INTEGER NOT NULL,

    descricao TEXT NOT NULL,

    quantidade REAL NOT NULL DEFAULT 1
        CHECK (quantidade > 0),

    unidade TEXT,

    fornecedor TEXT,

    observacao TEXT,

    valor REAL
        CHECK (valor IS NULL OR valor >= 0),

    ordem INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (orcamento_id)
        REFERENCES orcamentos(id)
        ON DELETE CASCADE
)

CREATE TABLE orcamento_itens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    orcamento_id INTEGER NOT NULL,

    acomodacao TEXT NOT NULL,

    descricao TEXT,

    quantidade REAL NOT NULL DEFAULT 1
        CHECK (quantidade > 0),

    unidade TEXT NOT NULL DEFAULT 'DIARIA',

    valor_unitario REAL NOT NULL DEFAULT 0
        CHECK (valor_unitario >= 0),

    valor_total REAL NOT NULL DEFAULT 0
        CHECK (valor_total >= 0),

    ordem INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (orcamento_id)
        REFERENCES orcamentos(id)
        ON DELETE CASCADE
)

CREATE TABLE orcamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    numero TEXT NOT NULL UNIQUE,

    tipo TEXT NOT NULL
        CHECK (tipo IN ('CONTA_ABERTA', 'PACOTE')),

    paciente_nome TEXT NOT NULL,

    paciente_contato TEXT,

    prontuario TEXT,

    medico_responsavel TEXT,

    procedimento TEXT,

    data_orcamento TEXT NOT NULL DEFAULT (date('now')),

    validade TEXT,

    forma_pagamento TEXT,

    observacao_pagamento TEXT,

    itens_inclusos TEXT,

    itens_exclusos TEXT,

    total REAL NOT NULL DEFAULT 0
        CHECK (total >= 0),

    status TEXT NOT NULL DEFAULT 'RASCUNHO'
        CHECK (
            status IN (
                'RASCUNHO',
                'FINALIZADO',
                'CANCELADO',
                'EXPIRADO'
            )
        ),

    criado_por INTEGER,

    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (criado_por)
        REFERENCES usuarios(id)
)

CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    login TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1
        CHECK (ativo IN (0,1)),
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)

CREATE VIEW vw_orcamentos AS
SELECT
    o.id,
    o.numero,
    o.tipo,
    o.paciente_nome,
    o.paciente_contato,
    o.prontuario,
    o.medico_responsavel,
    o.procedimento,
    o.data_orcamento,
    o.validade,
    o.total,
    o.status,
    u.nome AS criado_por_nome,
    o.criado_em,
    o.atualizado_em

FROM orcamentos AS o

LEFT JOIN usuarios AS u
    ON u.id = o.criado_por
