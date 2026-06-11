"""Persistencia SQLite para vendas do Cooper."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
from typing import Any, Iterator


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

    def resumo_hoje(self) -> dict[str, Any]:
        """Retorna um resumo das vendas registradas hoje em UTC."""
        agora = datetime.now(timezone.utc)
        inicio = agora.replace(hour=0, minute=0, second=0, microsecond=0)
        fim = inicio + timedelta(days=1)
        return self.resumo_periodo(
            inicio=inicio.isoformat(),
            fim=fim.isoformat(),
            nome_periodo="hoje",
        )

    def resumo_periodo(
        self,
        inicio: str,
        fim: str,
        nome_periodo: str,
    ) -> dict[str, Any]:
        """Retorna total vendido e itens agrupados por produto."""
        with self._conectar() as conexao:
            resumo = conexao.execute(
                """
                SELECT
                    COUNT(*) AS total_vendas,
                    COALESCE(SUM(quantidade), 0) AS quantidade_itens,
                    COALESCE(SUM(valor), 0) AS valor_total
                FROM vendas
                WHERE criado_em >= ? AND criado_em < ?
                """,
                (inicio, fim),
            ).fetchone()
            itens = conexao.execute(
                """
                SELECT
                    produto,
                    COUNT(*) AS total_vendas,
                    COALESCE(SUM(quantidade), 0) AS quantidade_itens,
                    COALESCE(SUM(valor), 0) AS valor_total
                FROM vendas
                WHERE criado_em >= ? AND criado_em < ?
                GROUP BY produto
                ORDER BY valor_total DESC, quantidade_itens DESC, produto
                """,
                (inicio, fim),
            ).fetchall()

        return {
            "tipo_relatorio": "vendas_periodo",
            "periodo": nome_periodo,
            "inicio": inicio,
            "fim": fim,
            "total_vendas": resumo["total_vendas"],
            "quantidade_itens": resumo["quantidade_itens"],
            "valor_total": resumo["valor_total"],
            "itens": [
                {
                    "produto": item["produto"],
                    "total_vendas": item["total_vendas"],
                    "quantidade_itens": item["quantidade_itens"],
                    "valor_total": item["valor_total"],
                }
                for item in itens
            ],
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
