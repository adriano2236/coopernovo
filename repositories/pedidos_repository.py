"""Persistencia SQLite para pedidos sob encomenda do Cooper."""

from contextlib import contextmanager
from datetime import datetime, timezone
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
                    entregue_em = CASE
                        WHEN ? = 'concluido' THEN COALESCE(entregue_em, ?)
                        ELSE entregue_em
                    END,
                    pago_em = CASE
                        WHEN ? = 'concluido' THEN COALESCE(pago_em, ?)
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
                    status,
                    agora,
                    pedido_id,
                ),
            )

        return self.buscar_por_id(pedido_id)

    def listar_pedidos_pendentes(self) -> list[dict[str, Any]]:
        """Lista pedidos ainda nao entregues."""
        return self._listar(
            """
            SELECT *
            FROM pedidos
            WHERE status NOT IN ('entregue', 'concluido')
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
                  AND status NOT IN ('entregue', 'concluido')
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
                    COALESCE(SUM(CASE WHEN status NOT IN ('entregue', 'concluido')
                        THEN MAX(COALESCE(preco_venda, 0) - COALESCE(valor_pago, 0), 0) ELSE 0 END), 0) AS valor_a_receber,
                    COALESCE(SUM(COALESCE(valor_pago, 0)), 0) AS valor_recebido,
                    COALESCE(SUM(CASE WHEN status IN ('pago_parcial', 'concluido')
                        AND custo_compra IS NOT NULL
                        THEN custo_compra ELSE 0 END), 0) AS custos_realizados,
                    COALESCE(SUM(CASE WHEN custo_compra IS NOT NULL
                        AND COALESCE(valor_pago, preco_venda) IS NOT NULL
                        THEN COALESCE(valor_pago, preco_venda) - custo_compra ELSE 0 END), 0) AS lucro_conhecido,
                    COALESCE(SUM(CASE WHEN status = 'concluido'
                        AND custo_compra IS NOT NULL
                        AND COALESCE(valor_pago, preco_venda) IS NOT NULL
                        THEN COALESCE(valor_pago, preco_venda) - custo_compra ELSE 0 END), 0) AS lucro_realizado
                FROM pedidos
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

        return self.buscar_por_id(pedido["pedido_id"]) or pedido

    def _buscar_pedido_aberto(
        self,
        cliente: str | None,
        produto: str | None = None,
    ) -> dict[str, Any] | None:
        cliente_normalizado = self._normalizar(cliente or "")
        produto_normalizado = self._normalizar(produto or "")

        filtros = ["status NOT IN ('entregue', 'concluido')"]
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
                    pago_em TEXT
                )
                """
            )
            self._garantir_coluna(conexao, "pedidos", "detalhe", "TEXT")
            self._garantir_coluna(conexao, "pedidos", "valor_pago", "REAL")
            self._garantir_coluna(conexao, "pedidos", "pago_em", "TEXT")

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

    def _agora(self) -> str:
        return datetime.now(timezone.utc).isoformat()
