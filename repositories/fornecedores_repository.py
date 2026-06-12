"""Persistencia SQLite para fornecedores do Cooper."""

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any, Iterator


class FornecedoresRepository:
    """Repositorio de fornecedores e produtos fornecidos."""

    def __init__(self, db_path: str | Path = "data/cooper.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._inicializar()

    def salvar_fornecedor(
        self,
        nome: str,
        telefone: str | None = None,
        endereco: str | None = None,
        observacoes: str | None = None,
    ) -> dict[str, Any]:
        """Cria ou atualiza um fornecedor pelo nome normalizado."""
        agora = self._agora()
        nome_limpo = " ".join((nome or "").strip().split())
        nome_normalizado = self._normalizar(nome_limpo)

        with self._conectar() as conexao:
            conexao.execute(
                """
                INSERT INTO fornecedores (
                    nome,
                    nome_normalizado,
                    telefone,
                    endereco,
                    observacoes,
                    criado_em,
                    atualizado_em
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(nome_normalizado)
                DO UPDATE SET
                    nome = excluded.nome,
                    telefone = COALESCE(excluded.telefone, fornecedores.telefone),
                    endereco = COALESCE(excluded.endereco, fornecedores.endereco),
                    observacoes = COALESCE(
                        excluded.observacoes,
                        fornecedores.observacoes
                    ),
                    atualizado_em = excluded.atualizado_em
                """,
                (
                    nome_limpo,
                    nome_normalizado,
                    telefone,
                    endereco,
                    observacoes,
                    agora,
                    agora,
                ),
            )

        fornecedor = self.buscar_por_nome(nome_limpo)
        return fornecedor or {
            "tipo_resultado": "fornecedor",
            "fornecedor": nome_limpo,
        }

    def salvar_produto_fornecedor(
        self,
        fornecedor: str,
        produto: str,
        atributos: dict[str, Any] | None = None,
        ultimo_custo: float | None = None,
        observacoes: str | None = None,
    ) -> dict[str, Any]:
        """Registra que um fornecedor trabalha com determinado produto."""
        fornecedor_salvo = self.salvar_fornecedor(fornecedor)
        fornecedor_id = int(fornecedor_salvo["fornecedor_id"])
        agora = self._agora()
        produto_limpo = " ".join((produto or "").strip().split())
        categoria = self._primeiro_atributo(atributos, "categoria")
        cor = self._primeiro_atributo(atributos, "cor")
        detalhe = self._atributo_texto(atributos, "detalhe")
        tamanho = self._primeiro_atributo(atributos, "tamanho")

        with self._conectar() as conexao:
            conexao.execute(
                """
                INSERT INTO fornecedor_produtos (
                    fornecedor_id,
                    produto,
                    produto_normalizado,
                    categoria,
                    cor,
                    detalhe,
                    tamanho,
                    ultimo_custo,
                    observacoes,
                    criado_em,
                    atualizado_em
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(fornecedor_id, produto_normalizado)
                DO UPDATE SET
                    produto = excluded.produto,
                    categoria = COALESCE(
                        excluded.categoria,
                        fornecedor_produtos.categoria
                    ),
                    cor = COALESCE(excluded.cor, fornecedor_produtos.cor),
                    detalhe = COALESCE(
                        excluded.detalhe,
                        fornecedor_produtos.detalhe
                    ),
                    tamanho = COALESCE(
                        excluded.tamanho,
                        fornecedor_produtos.tamanho
                    ),
                    ultimo_custo = COALESCE(
                        excluded.ultimo_custo,
                        fornecedor_produtos.ultimo_custo
                    ),
                    observacoes = COALESCE(
                        excluded.observacoes,
                        fornecedor_produtos.observacoes
                    ),
                    atualizado_em = excluded.atualizado_em
                """,
                (
                    fornecedor_id,
                    produto_limpo,
                    self._normalizar(produto_limpo),
                    categoria,
                    cor,
                    detalhe,
                    tamanho,
                    ultimo_custo,
                    observacoes,
                    agora,
                    agora,
                ),
            )

        produto_fornecedor = self.buscar_produto_do_fornecedor(
            fornecedor_id=fornecedor_id,
            produto=produto_limpo,
        )
        return produto_fornecedor or {
            "tipo_resultado": "fornecedor_produto",
            "fornecedor": fornecedor,
            "produto": produto_limpo,
        }

    def buscar_por_nome(self, nome: str) -> dict[str, Any] | None:
        """Busca fornecedor pelo nome."""
        with self._conectar() as conexao:
            linha = conexao.execute(
                """
                SELECT *
                FROM fornecedores
                WHERE nome_normalizado = ?
                """,
                (self._normalizar(nome),),
            ).fetchone()

        if not linha:
            return None

        fornecedor = self._fornecedor_dict(linha)
        fornecedor["produtos"] = self.listar_produtos_fornecedor(
            int(fornecedor["fornecedor_id"])
        )
        return fornecedor

    def buscar_produto_fornecedor(
        self,
        produto_fornecedor_id: int,
    ) -> dict[str, Any] | None:
        """Busca um vinculo fornecedor/produto por id."""
        with self._conectar() as conexao:
            linha = conexao.execute(
                """
                SELECT
                    fp.*,
                    f.nome AS fornecedor,
                    f.telefone AS telefone,
                    f.endereco AS endereco
                FROM fornecedor_produtos fp
                JOIN fornecedores f ON f.id = fp.fornecedor_id
                WHERE fp.id = ?
                """,
                (produto_fornecedor_id,),
            ).fetchone()

        return self._produto_fornecedor_dict(linha) if linha else None

    def buscar_produto_do_fornecedor(
        self,
        fornecedor_id: int,
        produto: str,
    ) -> dict[str, Any] | None:
        """Busca um produto especifico dentro de um fornecedor."""
        with self._conectar() as conexao:
            linha = conexao.execute(
                """
                SELECT
                    fp.*,
                    f.nome AS fornecedor,
                    f.telefone AS telefone,
                    f.endereco AS endereco
                FROM fornecedor_produtos fp
                JOIN fornecedores f ON f.id = fp.fornecedor_id
                WHERE fp.fornecedor_id = ?
                  AND fp.produto_normalizado = ?
                """,
                (fornecedor_id, self._normalizar(produto)),
            ).fetchone()

        return self._produto_fornecedor_dict(linha) if linha else None

    def buscar_por_produto(self, produto: str) -> list[dict[str, Any]]:
        """Lista fornecedores que trabalham com um produto."""
        produto_normalizado = self._normalizar(produto)
        tokens = [token for token in produto_normalizado.split() if token]
        if not tokens:
            return []

        filtros = []
        parametros: list[Any] = []
        for token in tokens:
            filtros.append("fp.produto_normalizado LIKE ?")
            parametros.append(f"%{token}%")

        sql = f"""
            SELECT
                fp.*,
                f.nome AS fornecedor,
                f.telefone AS telefone,
                f.endereco AS endereco
            FROM fornecedor_produtos fp
            JOIN fornecedores f ON f.id = fp.fornecedor_id
            WHERE {' AND '.join(filtros)}
            ORDER BY fp.atualizado_em DESC, f.nome
        """

        with self._conectar() as conexao:
            linhas = conexao.execute(sql, parametros).fetchall()

        return [self._produto_fornecedor_dict(linha) for linha in linhas]

    def listar_fornecedores(self, limite: int = 50) -> list[dict[str, Any]]:
        """Lista fornecedores cadastrados."""
        with self._conectar() as conexao:
            linhas = conexao.execute(
                """
                SELECT *
                FROM fornecedores
                ORDER BY atualizado_em DESC, nome
                LIMIT ?
                """,
                (limite,),
            ).fetchall()

        return [self._fornecedor_dict(linha) for linha in linhas]

    def listar_produtos_fornecedor(
        self,
        fornecedor_id: int,
    ) -> list[dict[str, Any]]:
        """Lista produtos associados a um fornecedor."""
        with self._conectar() as conexao:
            linhas = conexao.execute(
                """
                SELECT
                    fp.*,
                    f.nome AS fornecedor,
                    f.telefone AS telefone,
                    f.endereco AS endereco
                FROM fornecedor_produtos fp
                JOIN fornecedores f ON f.id = fp.fornecedor_id
                WHERE fp.fornecedor_id = ?
                ORDER BY fp.atualizado_em DESC, fp.produto
                """,
                (fornecedor_id,),
            ).fetchall()

        return [self._produto_fornecedor_dict(linha) for linha in linhas]

    def buscar_por_termo(
        self,
        termo: str,
        limite: int = 10,
    ) -> list[dict[str, Any]]:
        """Busca fornecedores por nome, contato, endereco ou observacoes."""
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
                    nome_normalizado LIKE ?
                    OR COALESCE(telefone, '') LIKE ?
                    OR LOWER(COALESCE(endereco, '')) LIKE ?
                    OR LOWER(COALESCE(observacoes, '')) LIKE ?
                )
                """
            )
            parametros.extend([like, like, like, like])

        parametros.append(limite)

        with self._conectar() as conexao:
            linhas = conexao.execute(
                f"""
                SELECT *
                FROM fornecedores
                WHERE {' AND '.join(filtros)}
                ORDER BY atualizado_em DESC, nome
                LIMIT ?
                """,
                parametros,
            ).fetchall()

        return [self._fornecedor_dict(linha) for linha in linhas]

    def buscar_produtos_por_termo(
        self,
        termo: str,
        limite: int = 10,
    ) -> list[dict[str, Any]]:
        """Busca produtos cadastrados dentro dos fornecedores."""
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
                    fp.produto_normalizado LIKE ?
                    OR LOWER(COALESCE(fp.categoria, '')) LIKE ?
                    OR LOWER(COALESCE(fp.cor, '')) LIKE ?
                    OR LOWER(COALESCE(fp.detalhe, '')) LIKE ?
                    OR LOWER(COALESCE(fp.tamanho, '')) LIKE ?
                    OR f.nome_normalizado LIKE ?
                )
                """
            )
            parametros.extend([like, like, like, like, like, like])

        parametros.append(limite)

        with self._conectar() as conexao:
            linhas = conexao.execute(
                f"""
                SELECT
                    fp.*,
                    f.nome AS fornecedor,
                    f.telefone AS telefone,
                    f.endereco AS endereco
                FROM fornecedor_produtos fp
                JOIN fornecedores f ON f.id = fp.fornecedor_id
                WHERE {' AND '.join(filtros)}
                ORDER BY fp.atualizado_em DESC, f.nome
                LIMIT ?
                """,
                parametros,
            ).fetchall()

        return [self._produto_fornecedor_dict(linha) for linha in linhas]

    def _inicializar(self) -> None:
        with self._conectar() as conexao:
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS fornecedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    nome_normalizado TEXT NOT NULL UNIQUE,
                    telefone TEXT,
                    endereco TEXT,
                    observacoes TEXT,
                    criado_em TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL
                )
                """
            )
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS fornecedor_produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fornecedor_id INTEGER NOT NULL,
                    produto TEXT NOT NULL,
                    produto_normalizado TEXT NOT NULL,
                    categoria TEXT,
                    cor TEXT,
                    detalhe TEXT,
                    tamanho TEXT,
                    ultimo_custo REAL,
                    observacoes TEXT,
                    criado_em TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL,
                    UNIQUE(fornecedor_id, produto_normalizado),
                    FOREIGN KEY(fornecedor_id) REFERENCES fornecedores(id)
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

    def _fornecedor_dict(self, linha: sqlite3.Row) -> dict[str, Any]:
        return {
            "tipo_resultado": "fornecedor",
            "fornecedor_id": linha["id"],
            "fornecedor": linha["nome"],
            "telefone": linha["telefone"],
            "endereco": linha["endereco"],
            "observacoes": linha["observacoes"],
            "criado_em": linha["criado_em"],
            "atualizado_em": linha["atualizado_em"],
        }

    def _produto_fornecedor_dict(self, linha: sqlite3.Row) -> dict[str, Any]:
        return {
            "tipo_resultado": "fornecedor_produto",
            "produto_fornecedor_id": linha["id"],
            "fornecedor_id": linha["fornecedor_id"],
            "fornecedor": linha["fornecedor"],
            "telefone": linha["telefone"],
            "endereco": linha["endereco"],
            "produto": linha["produto"],
            "categoria": linha["categoria"],
            "cor": linha["cor"],
            "detalhe": linha["detalhe"],
            "tamanho": linha["tamanho"],
            "ultimo_custo": linha["ultimo_custo"],
            "observacoes": linha["observacoes"],
            "criado_em": linha["criado_em"],
            "atualizado_em": linha["atualizado_em"],
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

    def _normalizar(self, valor: str) -> str:
        return " ".join((valor or "").strip().lower().split())

    def _tokens_busca(self, termo: str) -> list[str]:
        descartadas = {
            "a",
            "as",
            "da",
            "das",
            "de",
            "do",
            "dos",
            "fornecedor",
            "fornecedora",
            "fornecedores",
            "o",
            "os",
            "produto",
            "produtos",
        }
        return [
            token
            for token in self._normalizar(termo).split()
            if token and token not in descartadas
        ]

    def _agora(self) -> str:
        return datetime.now(timezone.utc).isoformat()
