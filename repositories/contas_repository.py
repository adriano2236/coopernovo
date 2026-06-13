"""Persistencia SQLite para contas a receber do Cooper."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
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

    def registrar_despesa(
        self,
        descricao: str,
        valor: float,
        categoria: str | None = None,
    ) -> dict[str, Any]:
        """Registra uma despesa paga e sua saida de caixa."""
        agora = self._agora()
        descricao_final = " ".join((descricao or "despesa avulsa").strip().split())
        categoria_final = categoria or "geral"

        with self._conectar() as conexao:
            cursor = conexao.execute(
                """
                INSERT INTO despesas (
                    descricao,
                    categoria,
                    valor,
                    criado_em,
                    atualizado_em
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    descricao_final,
                    categoria_final,
                    valor,
                    agora,
                    agora,
                ),
            )
            despesa_id = cursor.lastrowid
            conexao.execute(
                """
                INSERT INTO caixa_movimentos (
                    tipo,
                    origem,
                    referencia_id,
                    descricao,
                    valor,
                    criado_em
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "saida",
                    "despesa",
                    despesa_id,
                    descricao_final,
                    valor,
                    agora,
                ),
            )

        despesa = self.buscar_despesa(despesa_id)
        if despesa:
            despesa["saldo_caixa"] = self.saldo_caixa()
        return despesa or {"despesa_id": despesa_id}

    def registrar_movimento_caixa(
        self,
        tipo: str,
        valor: float,
        descricao: str | None = None,
        origem: str = "manual",
        referencia_id: int | None = None,
    ) -> dict[str, Any]:
        """Registra uma entrada ou saida no caixa."""
        tipo_normalizado = self._normalizar(tipo)
        if tipo_normalizado not in {"entrada", "saida"}:
            raise ValueError("tipo de movimento deve ser entrada ou saida")

        agora = self._agora()
        descricao_final = " ".join((descricao or tipo_normalizado).strip().split())
        with self._conectar() as conexao:
            cursor = conexao.execute(
                """
                INSERT INTO caixa_movimentos (
                    tipo,
                    origem,
                    referencia_id,
                    descricao,
                    valor,
                    criado_em
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    tipo_normalizado,
                    origem,
                    referencia_id,
                    descricao_final,
                    valor,
                    agora,
                ),
            )

        movimento = self.buscar_movimento_caixa(cursor.lastrowid)
        if movimento:
            movimento["saldo_caixa"] = self.saldo_caixa()
        return movimento or {"movimento_id": cursor.lastrowid}

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

    def saldo_caixa(self) -> float:
        """Calcula o saldo atual do caixa."""
        resumo = self.resumo_caixa()
        return float(resumo.get("caixa_saldo") or 0)

    def resumo_caixa(self) -> dict[str, Any]:
        """Resume entradas, saidas e saldo do caixa."""
        with self._conectar() as conexao:
            resumo = conexao.execute(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN tipo = 'entrada'
                        THEN valor ELSE 0 END), 0) AS caixa_entradas,
                    COALESCE(SUM(CASE WHEN tipo = 'saida'
                        THEN valor ELSE 0 END), 0) AS caixa_saidas,
                    COUNT(*) AS total_movimentos
                FROM caixa_movimentos
                """
            ).fetchone()

        entradas = float(resumo["caixa_entradas"] or 0)
        saidas = float(resumo["caixa_saidas"] or 0)
        return {
            "caixa_entradas": entradas,
            "caixa_saidas": saidas,
            "caixa_saldo": entradas - saidas,
            "total_movimentos_caixa": resumo["total_movimentos"],
        }

    def resumo_caixa_hoje(self) -> dict[str, Any]:
        """Resume entradas e saidas do caixa registradas hoje em UTC."""
        inicio, fim = self._periodo_hoje()
        return self.resumo_caixa_periodo(inicio, fim, "hoje")

    def resumo_caixa_periodo(
        self,
        inicio: str,
        fim: str,
        nome_periodo: str,
    ) -> dict[str, Any]:
        """Resume entradas e saidas do caixa dentro de um periodo."""
        with self._conectar() as conexao:
            resumo = conexao.execute(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN tipo = 'entrada'
                        THEN valor ELSE 0 END), 0) AS caixa_entradas,
                    COALESCE(SUM(CASE WHEN tipo = 'saida'
                        THEN valor ELSE 0 END), 0) AS caixa_saidas,
                    COUNT(*) AS total_movimentos
                FROM caixa_movimentos
                WHERE criado_em >= ? AND criado_em < ?
                """,
                (inicio, fim),
            ).fetchone()

        entradas = float(resumo["caixa_entradas"] or 0)
        saidas = float(resumo["caixa_saidas"] or 0)
        return {
            "periodo": nome_periodo,
            "inicio": inicio,
            "fim": fim,
            "caixa_entradas": entradas,
            "caixa_saidas": saidas,
            "caixa_saldo": entradas - saidas,
            "total_movimentos_caixa": resumo["total_movimentos"],
        }

    def resumo_despesas(self) -> dict[str, Any]:
        """Resume despesas registradas."""
        with self._conectar() as conexao:
            resumo = conexao.execute(
                """
                SELECT
                    COUNT(*) AS total_despesas,
                    COALESCE(SUM(valor), 0) AS valor_despesas
                FROM despesas
                """
            ).fetchone()

        return {
            "total_despesas": resumo["total_despesas"],
            "valor_despesas": resumo["valor_despesas"],
        }

    def resumo_despesas_hoje(self) -> dict[str, Any]:
        """Resume despesas registradas hoje em UTC."""
        inicio, fim = self._periodo_hoje()
        return self.resumo_despesas_periodo(inicio, fim, "hoje")

    def resumo_despesas_periodo(
        self,
        inicio: str,
        fim: str,
        nome_periodo: str,
    ) -> dict[str, Any]:
        """Resume despesas dentro de um periodo."""
        with self._conectar() as conexao:
            resumo = conexao.execute(
                """
                SELECT
                    COUNT(*) AS total_despesas,
                    COALESCE(SUM(valor), 0) AS valor_despesas
                FROM despesas
                WHERE criado_em >= ? AND criado_em < ?
                """,
                (inicio, fim),
            ).fetchone()

        return {
            "periodo": nome_periodo,
            "inicio": inicio,
            "fim": fim,
            "total_despesas": resumo["total_despesas"],
            "valor_despesas": resumo["valor_despesas"],
        }

    def listar_despesas(self, limite: int = 20) -> list[dict[str, Any]]:
        """Lista despesas recentes."""
        with self._conectar() as conexao:
            linhas = conexao.execute(
                """
                SELECT *
                FROM despesas
                ORDER BY criado_em DESC, id DESC
                LIMIT ?
                """,
                (limite,),
            ).fetchall()

        return [self._despesa_dict(linha) for linha in linhas]

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

    def buscar_despesa(self, despesa_id: int) -> dict[str, Any] | None:
        """Busca uma despesa pelo id."""
        with self._conectar() as conexao:
            linha = conexao.execute(
                "SELECT * FROM despesas WHERE id = ?",
                (despesa_id,),
            ).fetchone()

        return self._despesa_dict(linha) if linha else None

    def buscar_movimento_caixa(self, movimento_id: int) -> dict[str, Any] | None:
        """Busca um movimento de caixa pelo id."""
        with self._conectar() as conexao:
            linha = conexao.execute(
                "SELECT * FROM caixa_movimentos WHERE id = ?",
                (movimento_id,),
            ).fetchone()

        return self._caixa_movimento_dict(linha) if linha else None

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
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS despesas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descricao TEXT NOT NULL,
                    categoria TEXT,
                    valor REAL NOT NULL,
                    criado_em TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL
                )
                """
            )
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS caixa_movimentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    origem TEXT NOT NULL,
                    referencia_id INTEGER,
                    descricao TEXT,
                    valor REAL NOT NULL,
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

    def _despesa_dict(self, linha: sqlite3.Row) -> dict[str, Any]:
        return {
            "tipo_resultado": "despesa",
            "despesa_id": linha["id"],
            "descricao": linha["descricao"],
            "categoria": linha["categoria"],
            "valor": linha["valor"],
            "criado_em": linha["criado_em"],
            "atualizado_em": linha["atualizado_em"],
        }

    def _caixa_movimento_dict(self, linha: sqlite3.Row) -> dict[str, Any]:
        return {
            "tipo_resultado": "caixa_movimento",
            "movimento_id": linha["id"],
            "movimento_tipo": linha["tipo"],
            "origem": linha["origem"],
            "referencia_id": linha["referencia_id"],
            "descricao": linha["descricao"],
            "valor": linha["valor"],
            "criado_em": linha["criado_em"],
        }

    def _normalizar(self, valor: str) -> str:
        return " ".join((valor or "").strip().lower().split())

    def _periodo_hoje(self) -> tuple[str, str]:
        agora = datetime.now(timezone.utc)
        inicio = agora.replace(hour=0, minute=0, second=0, microsecond=0)
        fim = inicio + timedelta(days=1)
        return inicio.isoformat(), fim.isoformat()

    def _agora(self) -> str:
        return datetime.now(timezone.utc).isoformat()
