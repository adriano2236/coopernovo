"""Persistencia SQLite para vendas do Cooper."""

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any


class VendasRepository:
    """Repositorio simples para registrar vendas."""

    def __init__(self, db_path: str | Path = "data/cooper.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._inicializar()

    def registrar_venda(
        self,
        produto: str,
        quantidade: float,
        valor: float | None = None,
        produto_id: int | None = None,
    ) -> dict[str, Any]:
        """Registra uma venda e retorna os dados persistidos."""
        criado_em = datetime.now(timezone.utc).isoformat()

        with self._conectar() as conexao:
            cursor = conexao.execute(
                """
                INSERT INTO vendas (
                    produto_id,
                    produto,
                    quantidade,
                    valor,
                    criado_em
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    produto_id,
                    produto,
                    quantidade,
                    valor,
                    criado_em,
                ),
            )

        return {
            "venda_id": cursor.lastrowid,
            "produto_id": produto_id,
            "produto": produto,
            "quantidade_vendida": quantidade,
            "valor": valor,
            "criado_em": criado_em,
        }

    def _inicializar(self) -> None:
        with self._conectar() as conexao:
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS vendas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER,
                    produto TEXT NOT NULL,
                    quantidade REAL NOT NULL,
                    valor REAL,
                    criado_em TEXT NOT NULL
                )
                """
            )

    def _conectar(self) -> sqlite3.Connection:
        conexao = sqlite3.connect(self.db_path)
        conexao.row_factory = sqlite3.Row
        return conexao
