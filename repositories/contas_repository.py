"""Persistencia SQLite para contas a receber do Cooper."""

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any, Iterator


class ContasRepository:
    """Repositorio para dividas avulsas e pagamentos de clientes."""

    def __init__(self, db_path: str | Path = "data/cooper.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._inicializar()

    def registrar_divida(
        self,
        cliente: str,
        valor_total: float,
        descricao: str | None = None,
    ) -> dict[str, Any]:
        """Registra uma conta a receber de um cliente."""
        agora = self._agora()
        descricao_final = descricao or "conta avulsa"

        with self._conectar() as conexao:
            cursor = conexao.execute(
                """
                INSERT INTO contas_receber (
                    cliente,
                    cliente_normalizado,
                    descricao,
                    valor_total,
                    valor_pago,
                    status,
                    criado_em,
                    atualizado_em
                )
                VALUES (?, ?, ?, ?, 0, ?, ?, ?)
                """,
                (
                    cliente.strip(),
                    self._normalizar(cliente),
                    descricao_final,
                    valor_total,
                    "aberto",
                    agora,
                    agora,
                ),
            )

        conta = self.buscar_por_id(cursor.lastrowid)
        return conta or {"conta_id": cursor.lastrowid}

    def buscar_conta_aberta(
        self,
        cliente: str,
    ) -> dict[str, Any] | None:
        """Busca a conta aberta mais antiga do cliente."""
        return self._buscar_conta_aberta(cliente)

    def atualizar_pagamento(
        self,
        conta_id: int,
        valor_pago_total: float,
        status: str,
    ) -> dict[str, Any] | None:
        """Persiste o novo valor pago e status de uma conta."""
        agora = self._agora()

        with self._conectar() as conexao:
            conexao.execute(
                """
                UPDATE contas_receber
                SET valor_pago = ?,
                    status = ?,
                    atualizado_em = ?,
                    quitado_em = CASE
                        WHEN ? = 'quitado' THEN COALESCE(quitado_em, ?)
                        ELSE quitado_em
                    END
                WHERE id = ?
                """,
                (
                    valor_pago_total,
                    status,
                    agora,
                    status,
                    agora,
                    conta_id,
                ),
            )

        return self.buscar_por_id(conta_id)

    def resumo_cliente(self, cliente: str) -> dict[str, Any]:
        """Resume quanto um cliente ainda deve em contas avulsas."""
        cliente_normalizado = self._normalizar(cliente)
        with self._conectar() as conexao:
            resumo = conexao.execute(
                """
                SELECT
                    COUNT(*) AS total_contas,
                    COALESCE(SUM(valor_total), 0) AS valor_total,
                    COALESCE(SUM(valor_pago), 0) AS valor_pago,
                    COALESCE(SUM(MAX(valor_total - valor_pago, 0)), 0) AS valor_restante
                FROM contas_receber
                WHERE cliente_normalizado = ?
                  AND status != 'quitado'
                """,
                (cliente_normalizado,),
            ).fetchone()

        return {
            "tipo_resultado": "conta_resumo_cliente",
            "cliente": cliente,
            "total_contas": resumo["total_contas"],
            "valor_total": resumo["valor_total"],
            "valor_pago": resumo["valor_pago"],
            "valor_restante": resumo["valor_restante"],
        }

    def resumo(self) -> dict[str, Any]:
        """Resume contas avulsas abertas e pagas."""
        with self._conectar() as conexao:
            resumo = conexao.execute(
                """
                SELECT
                    COUNT(*) AS total_contas,
                    COALESCE(SUM(CASE WHEN status != 'quitado'
                        THEN MAX(valor_total - valor_pago, 0) ELSE 0 END), 0) AS valor_a_receber,
                    COALESCE(SUM(valor_pago), 0) AS valor_recebido
                FROM contas_receber
                """
            ).fetchone()

        return {
            "total_contas": resumo["total_contas"],
            "valor_a_receber": resumo["valor_a_receber"],
            "valor_recebido": resumo["valor_recebido"],
        }

    def listar_abertas(self) -> list[dict[str, Any]]:
        """Lista contas avulsas ainda nao quitadas."""
        with self._conectar() as conexao:
            linhas = conexao.execute(
                """
                SELECT *
                FROM contas_receber
                WHERE status != 'quitado'
                ORDER BY atualizado_em DESC, id DESC
                """
            ).fetchall()

        return [self._conta_dict(linha) for linha in linhas]

    def buscar_por_id(self, conta_id: int) -> dict[str, Any] | None:
        """Busca uma conta pelo id."""
        with self._conectar() as conexao:
            linha = conexao.execute(
                "SELECT * FROM contas_receber WHERE id = ?",
                (conta_id,),
            ).fetchone()

        return self._conta_dict(linha) if linha else None

    def _buscar_conta_aberta(self, cliente: str) -> dict[str, Any] | None:
        cliente_normalizado = self._normalizar(cliente)
        with self._conectar() as conexao:
            linha = conexao.execute(
                """
                SELECT *
                FROM contas_receber
                WHERE cliente_normalizado = ?
                  AND status != 'quitado'
                ORDER BY id ASC
                LIMIT 1
                """,
                (cliente_normalizado,),
            ).fetchone()

        return self._conta_dict(linha) if linha else None

    def _inicializar(self) -> None:
        with self._conectar() as conexao:
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS contas_receber (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente TEXT NOT NULL,
                    cliente_normalizado TEXT NOT NULL,
                    descricao TEXT,
                    valor_total REAL NOT NULL,
                    valor_pago REAL NOT NULL DEFAULT 0,
                    status TEXT NOT NULL,
                    criado_em TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL,
                    quitado_em TEXT
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

    def _conta_dict(self, linha: sqlite3.Row) -> dict[str, Any]:
        valor_total = linha["valor_total"]
        valor_pago = linha["valor_pago"]
        return {
            "tipo_resultado": "conta_receber",
            "conta_id": linha["id"],
            "cliente": linha["cliente"],
            "descricao": linha["descricao"],
            "valor_total": valor_total,
            "valor_pago": valor_pago,
            "status": linha["status"],
            "criado_em": linha["criado_em"],
            "atualizado_em": linha["atualizado_em"],
            "quitado_em": linha["quitado_em"],
        }

    def _normalizar(self, valor: str) -> str:
        return " ".join((valor or "").strip().lower().split())

    def _agora(self) -> str:
        return datetime.now(timezone.utc).isoformat()
