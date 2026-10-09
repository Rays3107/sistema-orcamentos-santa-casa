from pathlib import Path

import re

import sqlite3

from flask import Flask, jsonify, request, send_from_directory



BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "database" / "BDORCAMENTO.db"

FRONTEND_DIR = BASE_DIR / "frontend"



app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")





def get_db():

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON")

    ensure_schema_compatibility(conn)

    return conn







def ensure_schema_compatibility(conn):

    """Garante colunas novas sem apagar dados de bancos já utilizados."""

    cols = {

        row["name"]

        for row in conn.execute("PRAGMA table_info(orcamentos)").fetchall()

    }

    if "responsavel_nome" not in cols:

        conn.execute("ALTER TABLE orcamentos ADD COLUMN responsavel_nome TEXT")

        conn.commit()





def to_number(value, default=0.0):

    """Converte valores como 'R$ 1.234,56', '123,45' ou '01'."""

    if value is None or value == "":

        return default

    if isinstance(value, (int, float)):

        return float(value)



    text = str(value).strip()

    text = re.sub(r"[^\d,.\-]", "", text)



    if "," in text:

        text = text.replace(".", "").replace(",", ".")

    else:

        # Se houver vários pontos, considera o último como decimal.

        if text.count(".") > 1:

            parts = text.split(".")

            text = "".join(parts[:-1]) + "." + parts[-1]



    try:

        return float(text)

    except ValueError:

        return default





def parse_qty_unit(value):

    """

    Exemplos:

      '03 DIÁRIAS'       -> (3, 'DIARIA')

      '01 UNIDADE'       -> (1, 'UNIDADE')

      'ATÉ 02 DIÁRIAS'   -> (2, 'DIARIA')

      ''                 -> (1, 'UNIDADE')

    """

    text = str(value or "").strip()

    match = re.search(r"(\d+(?:[.,]\d+)?)", text)

    qty = to_number(match.group(1), 1) if match else 1



    upper = text.upper()

    if "DIÁRIA" in upper or "DIARIA" in upper:

        unit = "DIARIA"

    elif "UNIDADE" in upper:

        unit = "UNIDADE"

    elif "HORA" in upper:

        unit = "HORA"

    else:

        unit = "UNIDADE"



    return qty if qty > 0 else 1, unit





def normalize_type(value):

    text = str(value or "").strip().upper()

    if text in ("PACOTE", "PACKAGE"):

        return "PACOTE"

    return "CONTA_ABERTA"





def normalize_status(value):

    text = str(value or "RASCUNHO").strip().upper()

    allowed = {"RASCUNHO", "FINALIZADO", "CANCELADO", "EXPIRADO"}

    return text if text in allowed else "RASCUNHO"





@app.get("/")

def index():

    return send_from_directory(FRONTEND_DIR, "index.html")





@app.get("/api/health")

def health():

    return jsonify({

        "ok": True,

        "database": str(DB_PATH),

        "message": "Integração ativa"

    })





@app.get("/api/orcamentos")

def listar_orcamentos():

    conn = get_db()

    try:

        busca = str(request.args.get("q") or "").strip()

        tipo = normalize_type(request.args.get("tipo")) if request.args.get("tipo") else ""

        status = normalize_status(request.args.get("status")) if request.args.get("status") else ""



        sql = """

            SELECT

                o.id, o.numero, o.tipo, o.paciente_nome,

                o.paciente_contato, o.prontuario,

                o.medico_responsavel, o.responsavel_nome,

                o.procedimento, o.data_orcamento, o.validade,

                o.forma_pagamento, o.observacao_pagamento,

                o.total, o.status, o.criado_em, o.atualizado_em,

                u.nome AS criado_por_nome

            FROM orcamentos o

            LEFT JOIN usuarios u ON u.id = o.criado_por

            WHERE 1 = 1

        """

        params = []



        if busca:

            sql += """

                AND (

                    o.numero LIKE ?

                    OR o.paciente_nome LIKE ?

                    OR COALESCE(o.prontuario, '') LIKE ?

                )

            """

            like = f"%{busca}%"

            params.extend([like, like, like])



        if tipo in ("CONTA_ABERTA", "PACOTE"):

            sql += " AND o.tipo = ?"

            params.append(tipo)



        if status in ("RASCUNHO", "FINALIZADO", "CANCELADO", "EXPIRADO"):

            sql += " AND o.status = ?"

            params.append(status)



        sql += " ORDER BY o.id DESC"



        rows = conn.execute(sql, params).fetchall()

        return jsonify([dict(row) for row in rows])

    finally:

        conn.close()





@app.get("/api/orcamentos/<int:orcamento_id>")

def obter_orcamento(orcamento_id):

    conn = get_db()

    try:

        row = conn.execute("""

            SELECT

                o.*,

                u.nome AS criado_por_nome

            FROM orcamentos o

            LEFT JOIN usuarios u ON u.id = o.criado_por

            WHERE o.id = ?

        """, (orcamento_id,)).fetchone()



        if not row:

            return jsonify({"erro": "Orçamento não encontrado"}), 404



        result = dict(row)



        result["itens"] = [

            dict(r) for r in conn.execute("""

                SELECT * FROM orcamento_itens

                WHERE orcamento_id = ?

                ORDER BY ordem, id

            """, (orcamento_id,))

        ]



        result["exames"] = [

            dict(r) for r in conn.execute("""

                SELECT * FROM exames

                WHERE orcamento_id = ?

                ORDER BY ordem, id

            """, (orcamento_id,))

        ]



        result["opme"] = [

            dict(r) for r in conn.execute("""

                SELECT * FROM opme

                WHERE orcamento_id = ?

                ORDER BY ordem, id

            """, (orcamento_id,))

        ]



        result["historico"] = [

            dict(r) for r in conn.execute("""

                SELECT h.*, u.nome AS usuario_nome

                FROM historico_orcamento h

                LEFT JOIN usuarios u ON u.id = h.usuario_id

                WHERE h.orcamento_id = ?

                ORDER BY h.id DESC

            """, (orcamento_id,))

        ]



        return jsonify(result)

    finally:

        conn.close()





@app.post("/api/orcamentos")

def criar_orcamento():

    data = request.get_json(silent=True) or {}



    required = ["numero", "paciente_nome"]

    missing = [field for field in required if not str(data.get(field) or "").strip()]

    if missing:

        return jsonify({

            "erro": "Campos obrigatórios ausentes",

            "campos": missing

        }), 400



    numero = str(data["numero"]).strip()

    tipo = normalize_type(data.get("tipo"))

    paciente_nome = str(data["paciente_nome"]).strip()



    total = to_number(data.get("total"), 0)

    status = normalize_status(data.get("status"))

    criado_por = data.get("criado_por")



    # O formulário atual informa o nome do responsável, não o ID do usuário.

    # Por isso responsavel_nome é salvo normalmente e criado_por permanece NULL

    # até termos autenticação/usuários configurados.

    responsavel_nome = str(data.get("responsavel_nome") or "").strip() or None

    medico_responsavel = str(data.get("medico_responsavel") or responsavel_nome or "").strip() or None



    conn = get_db()



    try:

        cur = conn.cursor()



        cur.execute("""

            INSERT INTO orcamentos (

                numero,

                tipo,

                paciente_nome,

                paciente_contato,

                prontuario,

                medico_responsavel,

                responsavel_nome,

                procedimento,

                data_orcamento,

                validade,

                forma_pagamento,

                observacao_pagamento,

                itens_inclusos,

                itens_exclusos,

                total,

                status,

                criado_por

            )

               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        """, (

            numero,

            tipo,

            paciente_nome,

            data.get("paciente_contato"),

            data.get("prontuario"),

            medico_responsavel,

            responsavel_nome,

            data.get("procedimento"),

            data.get("data_orcamento") or None,

            data.get("validade") or None,

            data.get("forma_pagamento"),

            data.get("observacao_pagamento"),

            data.get("itens_inclusos"),

            data.get("itens_exclusos"),

            total,

            status,

            criado_por if criado_por not in ("", None) else None

        ))





        orcamento_id = cur.lastrowid



        # Itens da conta aberta ou do pacote.

        grupos = data.get("open") if tipo == "CONTA_ABERTA" else data.get("package")

        grupos = grupos if isinstance(grupos, list) else []



        ordem_item = 0

        for grupo in grupos:

            if not isinstance(grupo, dict):

                continue



            acomodacao = str(grupo.get("title") or "").strip() or "NÃO INFORMADO"

            itens = grupo.get("items")

            itens = itens if isinstance(itens, list) else []



            for item in itens:

                if not isinstance(item, dict):

                    continue



                nome = str(item.get("name") or "").strip()

                qty_text = str(item.get("qty") or "").strip()

                desc = str(item.get("desc") or "VALOR").strip() or "VALOR"

                valor = to_number(item.get("value"), 0)



                # Ignora linhas totalmente vazias.

                if not nome and not qty_text and valor == 0:

                    continue



                quantidade, unidade = parse_qty_unit(qty_text)



                cur.execute("""

                    INSERT INTO orcamento_itens (

                        orcamento_id,

                        acomodacao,

                        descricao,

                        quantidade,

                        unidade,

                        valor_unitario,

                        valor_total,

                        ordem

                    )

                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)

                """, (

                    orcamento_id,

                    acomodacao,

                    nome or desc,

                    quantidade,

                    unidade,

                    valor,

                    valor,

                    ordem_item

                ))

                ordem_item += 1



        # Exames

        exames = data.get("exams")

        exames = exames if isinstance(exames, list) else []



        for ordem, exame in enumerate(exames):

            if not isinstance(exame, dict):

                continue



            descricao = str(exame.get("name") or "").strip()

            valor = to_number(exame.get("value"), 0)



            if not descricao and valor == 0:

                continue



            cur.execute("""

                INSERT INTO exames (

                    orcamento_id,

                    descricao,

                    quantidade,

                    valor_unitario,

                    valor_total,

                    ordem

                )

                VALUES (?, ?, ?, ?, ?, ?)

            """, (

                orcamento_id,

                descricao or "EXAME",

                1,

                valor,

                valor,

                ordem

            ))



        # OPME

        opme = data.get("opme")

        if isinstance(opme, dict):

            descricao = str(opme.get("descricao") or "").strip()

            quantidade = to_number(opme.get("quantidade"), 1)

            observacao = str(opme.get("observacao") or "").strip() or None

            valor = opme.get("valor")

            valor = to_number(valor, 0) if valor not in (None, "") else None



            if descricao:

                cur.execute("""

                    INSERT INTO opme (

                        orcamento_id,

                        descricao,

                        quantidade,

                        unidade,

                        fornecedor,

                        observacao,

                        valor,

                        ordem

                    )

                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)

                """, (

                    orcamento_id,

                    descricao,

                    quantidade if quantidade > 0 else 1,

                    "UNIDADE",

                    None,

                    observacao,

                    valor,

                    0

                ))



        # Histórico inicial.

        descricao_historico = (

            f"Orçamento criado pelo formulário. "

            f"Responsável: {responsavel_nome or 'não informado'}."

        )



        cur.execute("""

            INSERT INTO historico_orcamento (

                orcamento_id,

                usuario_id,

                acao,

                descricao

            )

            VALUES (?, ?, ?, ?)

        """, (

            orcamento_id,

            criado_por if criado_por not in ("", None) else None,

            "CRIADO",

            descricao_historico

        ))



        conn.commit()



        return jsonify({

            "ok": True,

            "id": orcamento_id,

            "numero": numero,

            "message": "Orçamento gravado no banco com sucesso."

        }), 201



    except sqlite3.IntegrityError as exc:

        conn.rollback()

        return jsonify({

            "erro": str(exc),

            "tipo": "integrity_error"

        }), 409



    except Exception as exc:

        conn.rollback()

        return jsonify({

            "erro": str(exc),

            "tipo": "server_error"

        }), 500



    finally:

        conn.close()







@app.put("/api/orcamentos/<int:orcamento_id>")

def atualizar_orcamento(orcamento_id):

    data = request.get_json(silent=True) or {}



    required = ["numero", "paciente_nome"]

    missing = [field for field in required if not str(data.get(field) or "").strip()]

    if missing:

        return jsonify({

            "erro": "Campos obrigatórios ausentes",

            "campos": missing

        }), 400



    numero = str(data["numero"]).strip()

    tipo = normalize_type(data.get("tipo"))

    paciente_nome = str(data["paciente_nome"]).strip()

    total = to_number(data.get("total"), 0)

    status = normalize_status(data.get("status"))

    criado_por = data.get("criado_por")

    responsavel_nome = str(data.get("responsavel_nome") or "").strip() or None

    medico_responsavel = str(

        data.get("medico_responsavel") or responsavel_nome or ""

    ).strip() or None



    conn = get_db()



    try:

        cur = conn.cursor()



        existente = cur.execute(

            "SELECT id, criado_em FROM orcamentos WHERE id = ?",

            (orcamento_id,),

        ).fetchone()



        if not existente:

            return jsonify({"erro": "Orçamento não encontrado"}), 404



        # Evita conflito de número com outro orçamento.

        conflito = cur.execute(

            "SELECT id FROM orcamentos WHERE numero = ? AND id <> ?",

            (numero, orcamento_id),

        ).fetchone()

        if conflito:

            return jsonify({

                "erro": "Já existe outro orçamento com este número.",

                "tipo": "integrity_error"

            }), 409



        cur.execute("""

            UPDATE orcamentos

            SET

                numero = ?,

                tipo = ?,

                paciente_nome = ?,

                paciente_contato = ?,

                prontuario = ?,

                medico_responsavel = ?,

                responsavel_nome = ?,

                procedimento = ?,

                data_orcamento = ?,

                validade = ?,

                forma_pagamento = ?,

                observacao_pagamento = ?,

                itens_inclusos = ?,

                itens_exclusos = ?,

                total = ?,

                status = ?,

                atualizado_em = CURRENT_TIMESTAMP

            WHERE id = ?

        """, (

            numero,

            tipo,

            paciente_nome,

            data.get("paciente_contato"),

            data.get("prontuario"),

            medico_responsavel,

            responsavel_nome,

            data.get("procedimento"),

            data.get("data_orcamento") or None,

            data.get("validade") or None,

            data.get("forma_pagamento"),

            data.get("observacao_pagamento"),

            data.get("itens_inclusos"),

            data.get("itens_exclusos"),

            total,

            status,

            orcamento_id,

        ))



        # Recria os itens vinculados ao orçamento para manter a edição simples

        # e fiel ao que está no formulário.

        cur.execute("DELETE FROM orcamento_itens WHERE orcamento_id = ?", (orcamento_id,))

        cur.execute("DELETE FROM exames WHERE orcamento_id = ?", (orcamento_id,))

        cur.execute("DELETE FROM opme WHERE orcamento_id = ?", (orcamento_id,))



        grupos = data.get("open") if tipo == "CONTA_ABERTA" else data.get("package")

        grupos = grupos if isinstance(grupos, list) else []



        ordem_item = 0

        for grupo in grupos:

            if not isinstance(grupo, dict):

                continue



            acomodacao = str(grupo.get("title") or "").strip() or "NÃO INFORMADO"

            itens = grupo.get("items")

            itens = itens if isinstance(itens, list) else []



            for item in itens:

                if not isinstance(item, dict):

                    continue



                nome = str(item.get("name") or "").strip()

                qty_text = str(item.get("qty") or "").strip()

                desc = str(item.get("desc") or "VALOR").strip() or "VALOR"

                valor = to_number(item.get("value"), 0)



                if not nome and not qty_text and valor == 0:

                    continue



                quantidade, unidade = parse_qty_unit(qty_text)



                cur.execute("""

                    INSERT INTO orcamento_itens (

                        orcamento_id,

                        acomodacao,

                        descricao,

                        quantidade,

                        unidade,

                        valor_unitario,

                        valor_total,

                        ordem

                    )

                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)

                """, (

                    orcamento_id,

                    acomodacao,

                    nome or desc,

                    quantidade,

                    unidade,

                    valor,

                    valor,

                    ordem_item,

                ))

                ordem_item += 1



        exames = data.get("exams")

        exames = exames if isinstance(exames, list) else []



        for ordem, exame in enumerate(exames):

            if not isinstance(exame, dict):

                continue



            descricao = str(exame.get("name") or "").strip()

            valor = to_number(exame.get("value"), 0)



            if not descricao and valor == 0:

                continue



            cur.execute("""

                INSERT INTO exames (

                    orcamento_id,

                    descricao,

                    quantidade,

                    valor_unitario,

                    valor_total,

                    ordem

                )

                VALUES (?, ?, ?, ?, ?, ?)

            """, (

                orcamento_id,

                descricao or "EXAME",

                1,

                valor,

                valor,

                ordem,

            ))



        opme = data.get("opme")

        if isinstance(opme, dict):

            descricao = str(opme.get("descricao") or "").strip()

            quantidade = to_number(opme.get("quantidade"), 1)

            observacao = str(opme.get("observacao") or "").strip() or None

            valor = opme.get("valor")

            valor = to_number(valor, 0) if valor not in (None, "") else None



            if descricao:

                cur.execute("""

                    INSERT INTO opme (

                        orcamento_id,

                        descricao,

                        quantidade,

                        unidade,

                        fornecedor,

                        observacao,

                        valor,

                        ordem

                    )

                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)

                """, (

                    orcamento_id,

                    descricao,

                    quantidade if quantidade > 0 else 1,

                    "UNIDADE",

                    None,

                    observacao,

                    valor,

                    0,

                ))



        cur.execute("""

            INSERT INTO historico_orcamento (

                orcamento_id,

                usuario_id,

                acao,

                descricao

            )

            VALUES (?, ?, ?, ?)

        """, (

            orcamento_id,

            criado_por if criado_por not in ("", None) else None,

            "EDITADO",

            f"Orçamento atualizado pelo formulário. Responsável: {responsavel_nome or 'não informado'}.",

        ))



        conn.commit()



        return jsonify({

            "ok": True,

            "id": orcamento_id,

            "numero": numero,

            "message": "Orçamento atualizado no banco com sucesso.",

        })



    except sqlite3.IntegrityError as exc:

        conn.rollback()

        return jsonify({"erro": str(exc), "tipo": "integrity_error"}), 409



    except Exception as exc:

        conn.rollback()

        return jsonify({"erro": str(exc), "tipo": "server_error"}), 500



    finally:

        conn.close()





if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000, debug=True)
