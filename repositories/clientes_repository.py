"""Persistencia SQLite para clientes do Cooper."""

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any, Iterator


class ClientesRepository:
    """Repositorio de cadastro de clientes."""

    def __init__(self, db_path: str | Path = "data/cooper.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._inicializar()

    def salvar_cliente(
        self,
        nome: str,
        telefone: str | None = None,
        endereco: str | None = None,
        observacoes: str | None = None,
    ) -> dict[str, Any]:
        """Cria ou atualiza um cliente pelo nome normalizado."""
        agora = self._agora()
        nome_limpo = " ".join((nome or "").strip().split())
        nome_normalizado = self._normalizar(nome_limpo)

        with self._conectar() as conexao:
            conexao.execute(
                """
                INSERT INTO clientes (
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
                    telefone = COALESCE(excluded.telefone, clientes.telefone),
                    endereco = COALESCE(excluded.endereco, clientes.endereco),
                    observacoes = COALESCE(excluded.observacoes, clientes.observacoes),
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

        cliente = self.buscar_por_nome(nome_limpo)
        return cliente or {"tipo_resultado": "cliente", "cliente": nome_limpo}

    def atualizar_cliente(
        self,
        nome: str,
        telefone: str | None = None,
        endereco: str | None = None,
        observacoes: str | None = None,
    ) -> dict[str, Any] | None:
        """Atualiza campos informados de um cliente existente."""
        campos = []
        parametros: list[Any] = []

        if telefone is not None:
            campos.append("telefone = ?")
            parametros.append(telefone)

        if endereco is not None:
            campos.append("endereco = ?")
            parametros.append(endereco)

        if observacoes is not None:
            campos.append("observacoes = ?")
            parametros.append(observacoes)

        if not campos:
            return self.buscar_por_nome(nome)

        campos.append("atualizado_em = ?")
        parametros.append(self._agora())
        parametros.append(self._normalizar(nome))

        with self._conectar() as conexao:
            conexao.execute(
                f"""
                UPDATE clientes
                SET {', '.join(campos)}
                WHERE nome_normalizado = ?
                """,
                parametros,
            )

        return self.buscar_por_nome(nome)

    def buscar_por_nome(self, nome: str) -> dict[str, Any] | None:
        """Busca cliente pelo nome."""
        with self._conectar() as conexao:
            linha = conexao.execute(
                """
                SELECT *
                FROM clientes
                WHERE nome_normalizado = ?
                """,
                (self._normalizar(nome),),
            ).fetchone()

        return self._cliente_dict(linha) if linha else None

    def listar_clientes(self, limite: int = 50) -> list[dict[str, Any]]:
        """Lista clientes cadastrados."""
        with self._conectar() as conexao:
            linhas = conexao.execute(
                """
                SELECT *
                FROM clientes
                ORDER BY atualizado_em DESC, nome
                LIMIT ?
                """,
                (limite,),
            ).fetchall()

        return [self._cliente_dict(linha) for linha in linhas]

    def buscar_por_termo(
        self,
        termo: str,
        limite: int = 10,
    ) -> list[dict[str, Any]]:
        """Busca clientes por nome, telefone, endereco ou observacoes."""
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
                FROM clientes
                WHERE {' AND '.join(filtros)}
                ORDER BY atualizado_em DESC, nome
                LIMIT ?
                """,
                parametros,
            ).fetchall()

        return [self._cliente_dict(linha) for linha in linhas]

    def _inicializar(self) -> None:
        with self._conectar() as conexao:
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS clientes (
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

    def _cliente_dict(self, linha: sqlite3.Row) -> dict[str, Any]:
        return {
            "tipo_resultado": "cliente",
            "cliente_id": linha["id"],
            "cliente": linha["nome"],
            "telefone": linha["telefone"],
            "endereco": linha["endereco"],
            "observacoes": linha["observacoes"],
            "criado_em": linha["criado_em"],
            "atualizado_em": linha["atualizado_em"],
        }

    def _normalizar(self, valor: str) -> str:
        return " ".join((valor or "").strip().lower().split())

    def _tokens_busca(self, termo: str) -> list[str]:
        descartadas = {
            "a",
            "as",
            "cliente",
            "clientes",
            "da",
            "das",
            "de",
            "do",
            "dos",
            "o",
            "os",
        }
        return [
            token
            for token in self._normalizar(termo).split()
            if token and token not in descartadas
        ]

    def _agora(self) -> str:
        return datetime.now(timezone.utc).isoformat()
