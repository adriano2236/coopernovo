"""Persistencia SQLite para pedidos sob encomenda do Cooper."""

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterator


class PedidosRepository:
    """Repositorio para o fluxo de venda pre-confirmada."""

    def __init__(self, db_path: str | Path = "data/cooper.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._inicializar()

    def criar_pedido(
        self,
        cliente: str,
        produto: str,
        quantidade: float = 1,
        preco_venda: float | None = None,
        atributos: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Cria um pedido solicitado pelo cliente."""
        agora = self._agora()
        categoria = self._primeiro_atributo(atributos, "categoria")
        cor = self._primeiro_atributo(atributos, "cor")
        detalhe = self._atributo_texto(atributos, "detalhe")
        tamanho = self._primeiro_atributo(atributos, "tamanho")

        with self._conectar() as conexao:
            cursor = conexao.execute(
                """
                INSERT INTO pedidos (
                    cliente,
                    cliente_normalizado,
                    produto,
                    produto_normalizado,
                    categoria,
                    cor,
                    detalhe,
                    tamanho,
                    quantidade,
                    preco_venda,
                    status,
                    criado_em
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cliente.strip(),
                    self._normalizar(cliente),
                    produto.strip(),
                    self._normalizar(produto),
                    categoria,
                    cor,
                    detalhe,
                    tamanho,
                    quantidade,
                    preco_venda,
                    "solicitado",
                    agora,
                ),
            )

        pedido = self.buscar_por_id(cursor.lastrowid)
        pedido_id = int(cursor.lastrowid)
        self.registrar_historico(
            pedido_id=pedido_id,
            evento="pedido_criado",
            descricao=f"Pedido criado para {cliente.strip()}: {produto.strip()}",
            dados={
                "cliente": cliente.strip(),
                "produto": produto.strip(),
                "quantidade": quantidade,
                "preco_venda": preco_venda,
                "status": "solicitado",
            },
        )
        return pedido or {"pedido_id": cursor.lastrowid}

    def confirmar_pedido(
        self,
        cliente: str,
        produto: str | None = None,
    ) -> dict[str, Any]:
        """Marca o pedido mais recente do cliente como confirmado."""
        return self._atualizar_status(
            cliente=cliente,
            produto=produto,
            status="confirmado",
            campo_data="confirmado_em",
        )

    def registrar_compra(
        self,
        cliente: str | None,
        produto: str | None = None,
        custo_compra: float | None = None,
    ) -> dict[str, Any]:
        """Registra o custo de compra do pedido e marca como comprado."""
        pedido = self._buscar_pedido_aberto(cliente, produto)
        if pedido is None:
            return self._nao_encontrado(cliente, produto)

        agora = self._agora()
        with self._conectar() as conexao:
            conexao.execute(
                """
                UPDATE pedidos
                SET status = ?,
                    custo_compra = COALESCE(?, custo_compra),
                    comprado_em = ?
                WHERE id = ?
                """,
                ("comprado", custo_compra, agora, pedido["pedido_id"]),
            )

        self.registrar_historico(
            pedido_id=int(pedido["pedido_id"]),
            evento="compra_registrada",
            descricao="Compra do pedido registrada.",
            dados={
                "custo_compra": custo_compra,
                "status": "comprado",
            },
        )
        return self.buscar_por_id(pedido["pedido_id"]) or pedido

    def entregar_pedido(
        self,
        cliente: str,
        produto: str | None = None,
    ) -> dict[str, Any]:
        """Marca o pedido como entregue."""
        return self._atualizar_status(
            cliente=cliente,
            produto=produto,
            status="entregue",
            campo_data="entregue_em",
        )

    def buscar_pedido_aberto(
        self,
        cliente: str | None,
        produto: str | None = None,
    ) -> dict[str, Any] | None:
        """Busca o pedido aberto mais provavel para cliente/produto."""
        return self._buscar_pedido_aberto(cliente, produto)

    def buscar_mais_recente(
        self,
        cliente: str | None = None,
        produto: str | None = None,
    ) -> dict[str, Any] | None:
        """Busca o pedido mais recente por cliente e/ou produto."""
        cliente_normalizado = self._normalizar(cliente or "")
        produto_normalizado = self._normalizar(produto or "")

        filtros = []
        parametros: list[Any] = []

        if cliente_normalizado:
            filtros.append("cliente_normalizado = ?")
            parametros.append(cliente_normalizado)

        if produto_normalizado:
            filtros.append("produto_normalizado LIKE ?")
            parametros.append(f"%{produto_normalizado.split()[0]}%")

        where = ""
        if filtros:
            where = f"WHERE {' AND '.join(filtros)}"

        sql = f"""
            SELECT *
            FROM pedidos
            {where}
            ORDER BY id DESC
            LIMIT 10
        """

        with self._conectar() as conexao:
            linhas = conexao.execute(sql, parametros).fetchall()

        if not linhas:
            return None

        if produto_normalizado:
            tokens_produto = set(produto_normalizado.split())
            for linha in linhas:
                tokens_pedido = set(str(linha["produto_normalizado"]).split())
                if tokens_produto <= tokens_pedido:
                    return self._pedido_dict(linha)

        return self._pedido_dict(linhas[0])

    def atualizar_pagamento(
        self,
        pedido_id: int,
        preco_venda: float | None,
        valor_pago_total: float,
        status: str,
    ) -> dict[str, Any] | None:
        """Persiste pagamento e status calculados pelo agente."""
        agora = self._agora()
        with self._conectar() as conexao:
            conexao.execute(
                """
                UPDATE pedidos
                SET status = ?,
                    preco_venda = COALESCE(preco_venda, ?),
                    valor_pago = ?,
                    pago_em = CASE
                        WHEN ? IN ('pago', 'concluido') THEN COALESCE(pago_em, ?)
                        ELSE pago_em
                    END
                WHERE id = ?
                """,
                (
                    status,
                    preco_venda,
                    valor_pago_total,
                    status,
                    agora,
                    pedido_id,
                ),
            )

        self.registrar_historico(
            pedido_id=pedido_id,
            evento="pagamento_registrado",
            descricao="Pagamento do pedido registrado.",
            dados={
                "preco_venda": preco_venda,
                "valor_pago_total": valor_pago_total,
                "status": status,
            },
        )
        return self.buscar_por_id(pedido_id)

    def atualizar_entrega(
        self,
        pedido_id: int,
        status: str,
    ) -> dict[str, Any] | None:
        """Persiste a entrega do pedido com o status calculado pelo agente."""
        agora = self._agora()
        with self._conectar() as conexao:
            conexao.execute(
                """
                UPDATE pedidos
                SET status = ?,
                    entregue_em = COALESCE(entregue_em, ?)
                WHERE id = ?
                """,
                (status, agora, pedido_id),
            )

        self.registrar_historico(
            pedido_id=pedido_id,
            evento="entrega_registrada",
            descricao="Entrega do pedido registrada.",
            dados={"status": status},
        )
        return self.buscar_por_id(pedido_id)

    def atualizar_pedido(
        self,
        pedido_id: int,
        produto: str | None = None,
        quantidade: float | None = None,
        preco_venda: float | None = None,
        custo_compra: float | None = None,
        atributos: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Atualiza campos editaveis de um pedido."""
        campos = []
        parametros: list[Any] = []

        if produto is not None:
            campos.extend(["produto = ?", "produto_normalizado = ?"])
            parametros.extend([produto.strip(), self._normalizar(produto)])

        if quantidade is not None:
            campos.append("quantidade = ?")
            parametros.append(quantidade)

        if preco_venda is not None:
            campos.append("preco_venda = ?")
            parametros.append(preco_venda)

        if custo_compra is not None:
            campos.append("custo_compra = ?")
            parametros.append(custo_compra)

        if atributos:
            categoria = self._primeiro_atributo(atributos, "categoria")
            cor = self._primeiro_atributo(atributos, "cor")
            detalhe = self._atributo_texto(atributos, "detalhe")
            tamanho = self._primeiro_atributo(atributos, "tamanho")

            for campo, valor in (
                ("categoria", categoria),
                ("cor", cor),
                ("detalhe", detalhe),
                ("tamanho", tamanho),
            ):
                if valor is not None:
                    campos.append(f"{campo} = ?")
                    parametros.append(valor)

        if not campos:
            return self.buscar_por_id(pedido_id)

        parametros.append(pedido_id)
        with self._conectar() as conexao:
            conexao.execute(
                f"""
                UPDATE pedidos
                SET {', '.join(campos)}
                WHERE id = ?
                """,
                parametros,
            )

        self.registrar_historico(
            pedido_id=pedido_id,
            evento="pedido_editado",
            descricao="Pedido atualizado.",
            dados={
                "produto": produto,
                "quantidade": quantidade,
                "preco_venda": preco_venda,
                "custo_compra": custo_compra,
                "atributos": atributos or {},
            },
        )
        return self.buscar_por_id(pedido_id)

    def cancelar_pedido(
        self,
        pedido_id: int,
    ) -> dict[str, Any] | None:
        """Marca um pedido como cancelado."""
        agora = self._agora()
        with self._conectar() as conexao:
            conexao.execute(
                """
                UPDATE pedidos
                SET status = ?,
                    cancelado_em = COALESCE(cancelado_em, ?)
                WHERE id = ?
                """,
                ("cancelado", agora, pedido_id),
            )

        self.registrar_historico(
            pedido_id=pedido_id,
            evento="pedido_cancelado",
            descricao="Pedido cancelado.",
            dados={"status": "cancelado"},
        )
        return self.buscar_por_id(pedido_id)

    def listar_pedidos_pendentes(self) -> list[dict[str, Any]]:
        """Lista pedidos ainda nao entregues."""
        return self._listar(
            """
            SELECT *
            FROM pedidos
            WHERE status != 'concluido'
              AND status != 'cancelado'
            ORDER BY id DESC
            """
        )

    def listar_compras_pendentes(self) -> list[dict[str, Any]]:
        """Lista pedidos que ainda precisam de compra."""
        return self._listar(
            """
            SELECT *
            FROM pedidos
            WHERE status IN ('solicitado', 'confirmado')
            ORDER BY id DESC
            """
        )

    def listar_pedidos_concluidos(self) -> list[dict[str, Any]]:
        """Lista pedidos vendidos, pagos e encerrados."""
        return self._listar(
            """
            SELECT *
            FROM pedidos
            WHERE status = 'concluido'
            ORDER BY pago_em DESC, id DESC
            """
        )

    def buscar_por_termo(
        self,
        termo: str,
        limite: int = 10,
    ) -> list[dict[str, Any]]:
        """Busca pedidos por id, cliente, produto, variacao ou status."""
        tokens = self._tokens_busca(termo)
        if not tokens:
            return []

        filtros = []
        parametros: list[Any] = []
        ids = [int(token) for token in tokens if token.isdigit()]
        tokens_texto = [token for token in tokens if not token.isdigit()]

        for token in tokens_texto:
            like = f"%{token}%"
            filtros.append(
                """
                (
                    cliente_normalizado LIKE ?
                    OR produto_normalizado LIKE ?
                    OR LOWER(COALESCE(categoria, '')) LIKE ?
                    OR LOWER(COALESCE(cor, '')) LIKE ?
                    OR LOWER(COALESCE(detalhe, '')) LIKE ?
                    OR LOWER(COALESCE(tamanho, '')) LIKE ?
                    OR LOWER(COALESCE(status, '')) LIKE ?
                )
                """
            )
            parametros.extend([like, like, like, like, like, like, like])

        if ids:
            marcadores = ", ".join("?" for _ in ids)
            filtros.append(f"id IN ({marcadores})")
            parametros.extend(ids)

        if not filtros:
            return []

        parametros.append(limite)
        with self._conectar() as conexao:
            linhas = conexao.execute(
                f"""
                SELECT *
                FROM pedidos
                WHERE {' AND '.join(filtros)}
                ORDER BY id DESC
                LIMIT ?
                """,
                parametros,
            ).fetchall()

        return [self._pedido_dict(linha) for linha in linhas]

    def resumo_cliente(self, cliente: str) -> dict[str, Any]:
        """Resume valores em aberto de um cliente nos pedidos."""
        cliente_normalizado = self._normalizar(cliente)
        with self._conectar() as conexao:
            resumo = conexao.execute(
                """
                SELECT
                    COUNT(*) AS total_pedidos,
                    COALESCE(SUM(COALESCE(preco_venda, 0)), 0) AS valor_total,
                    COALESCE(SUM(COALESCE(valor_pago, 0)), 0) AS valor_pago,
                    COALESCE(SUM(MAX(COALESCE(preco_venda, 0) - COALESCE(valor_pago, 0), 0)), 0) AS valor_restante
                FROM pedidos
                WHERE cliente_normalizado = ?
                  AND status != 'concluido'
                  AND status != 'cancelado'
                """,
                (cliente_normalizado,),
            ).fetchone()

        return {
            "total_pedidos": resumo["total_pedidos"],
            "valor_total": resumo["valor_total"],
            "valor_pago": resumo["valor_pago"],
            "valor_restante": resumo["valor_restante"],
        }

    def resumo_financeiro(self) -> dict[str, Any]:
        """Resume valores a receber e lucro conhecido dos pedidos."""
        with self._conectar() as conexao:
            resumo = conexao.execute(
                """
                SELECT
                    COUNT(*) AS total_pedidos,
                    COALESCE(SUM(CASE WHEN status NOT IN ('concluido', 'cancelado')
                        THEN MAX(COALESCE(preco_venda, 0) - COALESCE(valor_pago, 0), 0) ELSE 0 END), 0) AS valor_a_receber,
                    COALESCE(SUM(COALESCE(valor_pago, 0)), 0) AS valor_recebido,
                    COALESCE(SUM(CASE WHEN custo_compra IS NOT NULL
                        THEN custo_compra ELSE 0 END), 0) AS custos_realizados,
                    COALESCE(SUM(CASE WHEN custo_compra IS NOT NULL
                        AND preco_venda IS NOT NULL
                        THEN preco_venda - custo_compra ELSE 0 END), 0) AS lucro_conhecido,
                    COALESCE(SUM(CASE WHEN status = 'concluido'
                        AND custo_compra IS NOT NULL
                        AND COALESCE(valor_pago, preco_venda) IS NOT NULL
                        THEN COALESCE(valor_pago, preco_venda) - custo_compra ELSE 0 END), 0) AS lucro_realizado
                FROM pedidos
                WHERE status != 'cancelado'
                """
            ).fetchone()

        return {
            "tipo_relatorio": "financeiro_pedidos",
            "total_pedidos": resumo["total_pedidos"],
            "valor_a_receber": resumo["valor_a_receber"],
            "valor_recebido": resumo["valor_recebido"],
            "custos_realizados": resumo["custos_realizados"],
            "lucro_conhecido": resumo["lucro_conhecido"],
            "lucro_realizado": resumo["lucro_realizado"],
        }

    def buscar_por_id(self, pedido_id: int) -> dict[str, Any] | None:
        """Busca um pedido pelo id."""
        with self._conectar() as conexao:
            linha = conexao.execute(
                "SELECT * FROM pedidos WHERE id = ?",
                (pedido_id,),
            ).fetchone()

        return self._pedido_dict(linha) if linha else None

    def registrar_historico(
        self,
        pedido_id: int,
        evento: str,
        descricao: str,
        dados: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Registra um evento historico de pedido."""
        agora = self._agora()
        with self._conectar() as conexao:
            cursor = conexao.execute(
                """
                INSERT INTO pedido_historico (
                    pedido_id,
                    evento,
                    descricao,
                    dados_json,
                    criado_em
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    pedido_id,
                    evento,
                    descricao,
                    self._json(dados or {}),
                    agora,
                ),
            )

        evento_historico = self.buscar_historico_por_id(cursor.lastrowid)
        return evento_historico or {"historico_id": cursor.lastrowid}

    def listar_historico(
        self,
        pedido_id: int,
    ) -> list[dict[str, Any]]:
        """Lista eventos de um pedido em ordem cronologica."""
        with self._conectar() as conexao:
            linhas = conexao.execute(
                """
                SELECT *
                FROM pedido_historico
                WHERE pedido_id = ?
                ORDER BY id ASC
                """,
                (pedido_id,),
            ).fetchall()

        return [self._historico_dict(linha) for linha in linhas]

    def buscar_historico_por_id(
        self,
        historico_id: int,
    ) -> dict[str, Any] | None:
        """Busca um evento historico por id."""
        with self._conectar() as conexao:
            linha = conexao.execute(
                "SELECT * FROM pedido_historico WHERE id = ?",
                (historico_id,),
            ).fetchone()

        return self._historico_dict(linha) if linha else None

    def _atualizar_status(
        self,
        cliente: str,
        produto: str | None,
        status: str,
        campo_data: str,
    ) -> dict[str, Any]:
        pedido = self._buscar_pedido_aberto(cliente, produto)
        if pedido is None:
            return self._nao_encontrado(cliente, produto)

        agora = self._agora()
        with self._conectar() as conexao:
            conexao.execute(
                f"UPDATE pedidos SET status = ?, {campo_data} = ? WHERE id = ?",
                (status, agora, pedido["pedido_id"]),
            )

        evento = "status_atualizado"
        descricao = f"Status do pedido alterado para {status}."
        if status == "confirmado":
            evento = "pedido_confirmado"
            descricao = "Pedido confirmado."
        if status == "entregue":
            evento = "entrega_registrada"
            descricao = "Entrega do pedido registrada."

        self.registrar_historico(
            pedido_id=int(pedido["pedido_id"]),
            evento=evento,
            descricao=descricao,
            dados={"status": status, "campo_data": campo_data},
        )
        return self.buscar_por_id(pedido["pedido_id"]) or pedido

    def _buscar_pedido_aberto(
        self,
        cliente: str | None,
        produto: str | None = None,
    ) -> dict[str, Any] | None:
        cliente_normalizado = self._normalizar(cliente or "")
        produto_normalizado = self._normalizar(produto or "")

        filtros = ["status NOT IN ('concluido', 'cancelado')"]
        parametros: list[Any] = []

        if cliente_normalizado:
            filtros.append("cliente_normalizado = ?")
            parametros.append(cliente_normalizado)

        if produto_normalizado:
            filtros.append("produto_normalizado LIKE ?")
            parametros.append(f"%{produto_normalizado.split()[0]}%")

        sql = f"""
            SELECT *
            FROM pedidos
            WHERE {' AND '.join(filtros)}
            ORDER BY id DESC
            LIMIT 1
        """

        with self._conectar() as conexao:
            linhas = conexao.execute(sql, parametros).fetchall()

        if not linhas:
            return None

        if produto_normalizado:
            tokens_produto = set(produto_normalizado.split())
            for linha in linhas:
                tokens_pedido = set(str(linha["produto_normalizado"]).split())
                if tokens_produto <= tokens_pedido:
                    return self._pedido_dict(linha)

        return self._pedido_dict(linhas[0])

    def _listar(self, sql: str) -> list[dict[str, Any]]:
        with self._conectar() as conexao:
            linhas = conexao.execute(sql).fetchall()

        return [self._pedido_dict(linha) for linha in linhas]

    def _inicializar(self) -> None:
        with self._conectar() as conexao:
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS pedidos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente TEXT NOT NULL,
                    cliente_normalizado TEXT NOT NULL,
                    produto TEXT NOT NULL,
                    produto_normalizado TEXT NOT NULL,
                    categoria TEXT,
                    cor TEXT,
                    detalhe TEXT,
                    tamanho TEXT,
                    quantidade REAL NOT NULL DEFAULT 1,
                    preco_venda REAL,
                    custo_compra REAL,
                    valor_pago REAL,
                    status TEXT NOT NULL,
                    criado_em TEXT NOT NULL,
                    confirmado_em TEXT,
                    comprado_em TEXT,
                    entregue_em TEXT,
                    pago_em TEXT,
                    cancelado_em TEXT
                )
                """
            )
            self._garantir_coluna(conexao, "pedidos", "detalhe", "TEXT")
            self._garantir_coluna(conexao, "pedidos", "valor_pago", "REAL")
            self._garantir_coluna(conexao, "pedidos", "pago_em", "TEXT")
            self._garantir_coluna(conexao, "pedidos", "cancelado_em", "TEXT")
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS pedido_historico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pedido_id INTEGER NOT NULL,
                    evento TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    dados_json TEXT,
                    criado_em TEXT NOT NULL,
                    FOREIGN KEY(pedido_id) REFERENCES pedidos(id)
                )
                """
            )

    @contextmanager
    def _conectar(self) -> Iterator[sqlite3.Connection]:
        conexao = sqlite3.connect(self.db_path)
        conexao.row_factory = sqlite3.Row
        try:
            yield conexao
            conexao.commit()
        except Exception:
            conexao.rollback()
            raise
        finally:
            conexao.close()

    def _pedido_dict(self, linha: sqlite3.Row) -> dict[str, Any]:
        preco = linha["preco_venda"]
        custo = linha["custo_compra"]
        valor_pago = linha["valor_pago"]

        return {
            "tipo_resultado": "pedido",
            "pedido_id": linha["id"],
            "cliente": linha["cliente"],
            "produto": linha["produto"],
            "categoria": linha["categoria"],
            "cor": linha["cor"],
            "detalhe": linha["detalhe"],
            "tamanho": linha["tamanho"],
            "quantidade": linha["quantidade"],
            "preco_venda": preco,
            "custo_compra": custo,
            "valor_pago": valor_pago,
            "status": linha["status"],
            "criado_em": linha["criado_em"],
            "confirmado_em": linha["confirmado_em"],
            "comprado_em": linha["comprado_em"],
            "entregue_em": linha["entregue_em"],
            "pago_em": linha["pago_em"],
            "cancelado_em": linha["cancelado_em"],
        }

    def _historico_dict(self, linha: sqlite3.Row) -> dict[str, Any]:
        return {
            "historico_id": linha["id"],
            "pedido_id": linha["pedido_id"],
            "evento": linha["evento"],
            "descricao": linha["descricao"],
            "dados": self._from_json(linha["dados_json"]),
            "criado_em": linha["criado_em"],
        }

    def _nao_encontrado(
        self,
        cliente: str | None,
        produto: str | None,
    ) -> dict[str, Any]:
        return {
            "tipo_resultado": "pedido_nao_encontrado",
            "cliente": cliente,
            "produto": produto,
            "pedido_encontrado": False,
        }

    def _primeiro_atributo(
        self,
        atributos: dict[str, Any] | None,
        nome: str,
    ) -> str | None:
        valor = (atributos or {}).get(nome)
        if isinstance(valor, list):
            return str(valor[0]) if valor else None
        if valor:
            return str(valor)
        return None

    def _atributo_texto(
        self,
        atributos: dict[str, Any] | None,
        nome: str,
    ) -> str | None:
        valor = (atributos or {}).get(nome)
        if isinstance(valor, list):
            return " ".join(str(item) for item in valor if item) or None
        if valor:
            return str(valor)
        return None

    def _garantir_coluna(
        self,
        conexao: sqlite3.Connection,
        tabela: str,
        coluna: str,
        tipo: str,
    ) -> None:
        colunas = {
            linha["name"]
            for linha in conexao.execute(f"PRAGMA table_info({tabela})").fetchall()
        }
        if coluna not in colunas:
            conexao.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")

    def _normalizar(self, valor: str) -> str:
        return " ".join((valor or "").strip().lower().split())

    def _tokens_busca(self, termo: str) -> list[str]:
        descartadas = {
            "a",
            "as",
            "cliente",
            "da",
            "das",
            "de",
            "do",
            "dos",
            "n",
            "numero",
            "o",
            "os",
            "pedido",
            "pedidos",
            "produto",
            "produtos",
        }
        return [
            token
            for token in self._normalizar(termo).replace("#", " ").split()
            if token and token not in descartadas
        ]

    def _json(self, valor: dict[str, Any]) -> str:
        return json.dumps(valor, ensure_ascii=False, default=str)

    def _from_json(self, valor: str | None) -> dict[str, Any]:
        if not valor:
            return {}
        try:
            dados = json.loads(valor)
        except json.JSONDecodeError:
            return {}
        return dados if isinstance(dados, dict) else {}

    def _agora(self) -> str:
        return datetime.now(timezone.utc).isoformat()
