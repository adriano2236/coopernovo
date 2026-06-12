"""Persistencia SQLite para o estoque do Cooper."""

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any, Iterator


class EstoqueRepository:
    """Repositorio de estoque usando produtos, saldos e movimentos."""

    def __init__(self, db_path: str | Path = "data/cooper.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._inicializar()

    def consultar(
        self,
        produto: str,
        atributos: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Consulta o saldo de uma variacao de produto."""
        produto_id = self._buscar_produto_id(produto, atributos)
        if produto_id is None:
            return None

        with self._conectar() as conexao:
            linha = conexao.execute(
                """
                SELECT
                    p.id,
                    p.nome,
                    p.categoria,
                    p.cor,
                    p.tamanho,
                    p.sku,
                    COALESCE(e.quantidade, 0) AS quantidade
                FROM produtos p
                LEFT JOIN estoque e ON e.produto_id = p.id
                WHERE p.id = ?
                """,
                (produto_id,),
            ).fetchone()

        return self._produto_com_saldo(linha) if linha else None

    def listar(self) -> list[dict[str, Any]]:
        """Lista todas as variacoes de produto cadastradas no estoque."""
        with self._conectar() as conexao:
            linhas = conexao.execute(
                """
                SELECT
                    p.id,
                    p.nome,
                    p.categoria,
                    p.cor,
                    p.tamanho,
                    p.sku,
                    COALESCE(e.quantidade, 0) AS quantidade
                FROM produtos p
                LEFT JOIN estoque e ON e.produto_id = p.id
                ORDER BY p.nome, p.cor, p.tamanho
                """
            ).fetchall()

        return [self._produto_com_saldo(linha) for linha in linhas]

    def listar_estoque_baixo(self, limite: float = 3) -> list[dict[str, Any]]:
        """Lista produtos com saldo menor ou igual ao limite informado."""
        with self._conectar() as conexao:
            linhas = conexao.execute(
                """
                SELECT
                    p.id,
                    p.nome,
                    p.categoria,
                    p.cor,
                    p.tamanho,
                    p.sku,
                    COALESCE(e.quantidade, 0) AS quantidade
                FROM produtos p
                LEFT JOIN estoque e ON e.produto_id = p.id
                WHERE COALESCE(e.quantidade, 0) <= ?
                ORDER BY quantidade ASC, p.nome, p.cor, p.tamanho
                """,
                (limite,),
            ).fetchall()

        return [self._produto_com_saldo(linha) for linha in linhas]

    def buscar_por_termo(
        self,
        termo: str,
        limite: int = 10,
    ) -> list[dict[str, Any]]:
        """Busca produtos cadastrados no estoque por texto livre."""
        tokens = self._tokens_busca(termo)
        if not tokens:
            return []

        filtros = []
        parametros: list[Any] = []
        for token in tokens:
            like = f"%{token}%"
            filtros.append(
                """
                (
                    p.nome_normalizado LIKE ?
                    OR LOWER(COALESCE(p.categoria, '')) LIKE ?
                    OR LOWER(COALESCE(p.cor, '')) LIKE ?
                    OR LOWER(COALESCE(p.tamanho, '')) LIKE ?
                    OR LOWER(COALESCE(p.sku, '')) LIKE ?
                )
                """
            )
            parametros.extend([like, like, like, like, like])

        parametros.append(limite)

        with self._conectar() as conexao:
            linhas = conexao.execute(
                f"""
                SELECT
                    p.id,
                    p.nome,
                    p.categoria,
                    p.cor,
                    p.tamanho,
                    p.sku,
                    COALESCE(e.quantidade, 0) AS quantidade
                FROM produtos p
                LEFT JOIN estoque e ON e.produto_id = p.id
                WHERE {' AND '.join(filtros)}
                ORDER BY p.nome, p.cor, p.tamanho
                LIMIT ?
                """,
                parametros,
            ).fetchall()

        return [self._produto_com_saldo(linha) for linha in linhas]

    def historico(
        self,
        produto: str,
        atributos: dict[str, Any] | None = None,
        limite: int = 10,
    ) -> dict[str, Any] | None:
        """Retorna os movimentos recentes de uma variacao de produto."""
        item = self.consultar(produto, atributos)
        if item is None:
            return None

        with self._conectar() as conexao:
            linhas = conexao.execute(
                """
                SELECT
                    id,
                    tipo,
                    quantidade,
                    quantidade_anterior,
                    quantidade_atual,
                    criado_em
                FROM estoque_movimentos
                WHERE produto_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (item["produto_id"], limite),
            ).fetchall()

        return {
            "produto": item,
            "movimentos": [
                {
                    "movimento_id": linha["id"],
                    "tipo": linha["tipo"],
                    "quantidade": linha["quantidade"],
                    "quantidade_anterior": linha["quantidade_anterior"],
                    "quantidade_atual": linha["quantidade_atual"],
                    "criado_em": linha["criado_em"],
                }
                for linha in linhas
            ],
        }

    def registrar_entrada(
        self,
        produto: str,
        quantidade: float,
        atributos: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Soma quantidade ao saldo do produto e registra o movimento."""
        return self._registrar_movimento(
            produto=produto,
            quantidade=abs(quantidade),
            tipo="entrada",
            atributos=atributos,
        )

    def registrar_saida(
        self,
        produto: str,
        quantidade: float,
        atributos: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Subtrai quantidade do saldo quando houver estoque suficiente."""
        quantidade_saida = abs(quantidade)
        produto_id = self._buscar_produto_id(produto, atributos)

        if produto_id is None:
            return {
                "produto": produto,
                "quantidade_anterior": 0,
                "quantidade_atual": 0,
                "quantidade_movimentada": quantidade_saida,
                "movimento_realizado": False,
                "motivo": "produto_nao_cadastrado",
            }

        saldo_atual = self._saldo_atual(produto_id)
        if saldo_atual < quantidade_saida:
            return {
                "produto": produto,
                "quantidade_anterior": saldo_atual,
                "quantidade_atual": saldo_atual,
                "quantidade_movimentada": quantidade_saida,
                "movimento_realizado": False,
                "motivo": "saldo_insuficiente",
            }

        return self._registrar_movimento(
            produto=produto,
            quantidade=quantidade_saida,
            tipo="saida",
            atributos=atributos,
        )

    def _registrar_movimento(
        self,
        produto: str,
        quantidade: float,
        tipo: str,
        atributos: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if quantidade <= 0:
            raise ValueError("quantidade deve ser maior que zero.")

        produto_id = self._obter_ou_criar_produto(produto, atributos)
        quantidade_anterior = self._saldo_atual(produto_id)
        delta = quantidade if tipo == "entrada" else -quantidade
        quantidade_atual = quantidade_anterior + delta
        criado_em = datetime.now(timezone.utc).isoformat()

        with self._conectar() as conexao:
            conexao.execute(
                """
                INSERT INTO estoque (produto_id, quantidade)
                VALUES (?, ?)
                ON CONFLICT(produto_id)
                DO UPDATE SET quantidade = excluded.quantidade
                """,
                (produto_id, quantidade_atual),
            )
            cursor = conexao.execute(
                """
                INSERT INTO estoque_movimentos (
                    produto_id,
                    tipo,
                    quantidade,
                    quantidade_anterior,
                    quantidade_atual,
                    criado_em
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    produto_id,
                    tipo,
                    quantidade,
                    quantidade_anterior,
                    quantidade_atual,
                    criado_em,
                ),
            )

        item = self.consultar(produto, atributos) or {"produto": produto}
        return {
            **item,
            "quantidade_anterior": quantidade_anterior,
            "quantidade_atual": quantidade_atual,
            "quantidade_movimentada": quantidade,
            "movimento_tipo": tipo,
            "movimento_id": cursor.lastrowid,
            "movimento_realizado": True,
            "criado_em": criado_em,
        }

    def _obter_ou_criar_produto(
        self,
        produto: str,
        atributos: dict[str, Any] | None,
    ) -> int:
        nome = self._normalizar_produto(produto)
        if not nome:
            raise ValueError("produto deve ser informado.")

        categoria = self._primeiro_atributo(atributos, "categoria")
        cor = self._primeiro_atributo(atributos, "cor")
        tamanho = self._primeiro_atributo(atributos, "tamanho")
        chave = self._chave_produto(nome, categoria, cor, tamanho)
        sku = self._gerar_sku(categoria, cor, tamanho, nome)

        with self._conectar() as conexao:
            conexao.execute(
                """
                INSERT INTO produtos (
                    nome,
                    nome_normalizado,
                    categoria,
                    cor,
                    tamanho,
                    sku,
                    chave
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chave)
                DO UPDATE SET
                    nome = excluded.nome,
                    categoria = excluded.categoria,
                    cor = excluded.cor,
                    tamanho = excluded.tamanho,
                    sku = excluded.sku
                """,
                (
                    produto.strip(),
                    nome,
                    categoria,
                    cor,
                    tamanho,
                    sku,
                    chave,
                ),
            )
            linha = conexao.execute(
                "SELECT id FROM produtos WHERE chave = ?",
                (chave,),
            ).fetchone()

        return int(linha["id"])

    def _buscar_produto_id(
        self,
        produto: str,
        atributos: dict[str, Any] | None,
    ) -> int | None:
        nome = self._normalizar_produto(produto)
        if not nome:
            return None

        categoria = self._primeiro_atributo(atributos, "categoria")
        cor = self._primeiro_atributo(atributos, "cor")
        tamanho = self._primeiro_atributo(atributos, "tamanho")
        chave = self._chave_produto(nome, categoria, cor, tamanho)

        with self._conectar() as conexao:
            linha = conexao.execute(
                "SELECT id FROM produtos WHERE chave = ?",
                (chave,),
            ).fetchone()

        return int(linha["id"]) if linha else None

    def _saldo_atual(self, produto_id: int) -> float:
        with self._conectar() as conexao:
            linha = conexao.execute(
                "SELECT quantidade FROM estoque WHERE produto_id = ?",
                (produto_id,),
            ).fetchone()

        return float(linha["quantidade"]) if linha else 0.0

    def _inicializar(self) -> None:
        with self._conectar() as conexao:
            estoque_antigo = self._estoque_antigo(conexao)
            if estoque_antigo:
                conexao.execute("ALTER TABLE estoque RENAME TO estoque_legado")

            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    nome_normalizado TEXT NOT NULL,
                    categoria TEXT,
                    cor TEXT,
                    tamanho TEXT,
                    sku TEXT,
                    chave TEXT NOT NULL UNIQUE
                )
                """
            )
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS estoque (
                    produto_id INTEGER PRIMARY KEY,
                    quantidade REAL NOT NULL DEFAULT 0,
                    FOREIGN KEY (produto_id) REFERENCES produtos(id)
                )
                """
            )

            if estoque_antigo:
                self._migrar_estoque_legado(conexao)
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS estoque_movimentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL,
                    quantidade REAL NOT NULL,
                    quantidade_anterior REAL NOT NULL,
                    quantidade_atual REAL NOT NULL,
                    criado_em TEXT NOT NULL,
                    FOREIGN KEY (produto_id) REFERENCES produtos(id)
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

    def _estoque_antigo(self, conexao: sqlite3.Connection) -> bool:
        tabela = conexao.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'estoque'
            """
        ).fetchone()
        if tabela is None:
            return False

        colunas = {
            linha["name"]
            for linha in conexao.execute("PRAGMA table_info(estoque)").fetchall()
        }
        return "produto_id" not in colunas

    def _migrar_estoque_legado(self, conexao: sqlite3.Connection) -> None:
        linhas = conexao.execute(
            """
            SELECT produto, quantidade
            FROM estoque_legado
            """
        ).fetchall()

        for linha in linhas:
            produto = str(linha["produto"])
            nome = self._normalizar_produto(produto)
            chave = self._chave_produto(nome, None, None, None)
            sku = self._gerar_sku(None, None, None, nome)
            conexao.execute(
                """
                INSERT INTO produtos (
                    nome,
                    nome_normalizado,
                    categoria,
                    cor,
                    tamanho,
                    sku,
                    chave
                )
                VALUES (?, ?, NULL, NULL, NULL, ?, ?)
                ON CONFLICT(chave) DO NOTHING
                """,
                (produto, nome, sku, chave),
            )
            produto_id = conexao.execute(
                "SELECT id FROM produtos WHERE chave = ?",
                (chave,),
            ).fetchone()["id"]
            conexao.execute(
                """
                INSERT INTO estoque (produto_id, quantidade)
                VALUES (?, ?)
                ON CONFLICT(produto_id)
                DO UPDATE SET quantidade = excluded.quantidade
                """,
                (produto_id, linha["quantidade"]),
            )

    def _produto_com_saldo(self, linha: sqlite3.Row) -> dict[str, Any]:
        return {
            "produto_id": linha["id"],
            "produto": linha["nome"],
            "categoria": linha["categoria"],
            "cor": linha["cor"],
            "tamanho": linha["tamanho"],
            "sku": linha["sku"],
            "quantidade": linha["quantidade"],
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

    def _chave_produto(
        self,
        nome: str,
        categoria: str | None,
        cor: str | None,
        tamanho: str | None,
    ) -> str:
        partes = [nome, categoria or "", cor or "", tamanho or ""]
        return "|".join(partes)

    def _gerar_sku(
        self,
        categoria: str | None,
        cor: str | None,
        tamanho: str | None,
        nome: str,
    ) -> str:
        partes = [categoria or nome, cor or "sem-cor", tamanho or "sem-tamanho"]
        return "-".join(self._normalizar_produto(parte).replace(" ", "-") for parte in partes)

    def _normalizar_produto(self, produto: str) -> str:
        return " ".join((produto or "").strip().lower().split())

    def _tokens_busca(self, termo: str) -> list[str]:
        descartadas = {
            "a",
            "as",
            "da",
            "das",
            "de",
            "do",
            "dos",
            "estoque",
            "o",
            "os",
            "produto",
            "produtos",
            "saldo",
        }
        return [
            token
            for token in self._normalizar_produto(termo).split()
            if token and token not in descartadas
        ]
