"""Persistencia SQLite para memorias do Cooper."""

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterator


class MemoriaRepository:
    """Repositorio de memorias e eventos historicos."""

    def __init__(self, db_path: str | Path = "data/cooper.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._inicializar()

    def registrar_memoria(
        self,
        fase: int,
        tipo: str,
        chave: str,
        valor: str,
        origem: str,
        importancia: int = 1,
        metadados: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Insere uma memoria ativa no banco."""
        agora = self._agora()
        with self._conectar() as conexao:
            cursor = conexao.execute(
                """
                INSERT INTO memorias (
                    fase,
                    tipo,
                    chave,
                    valor,
                    origem,
                    importancia,
                    ativa,
                    metadados_json,
                    criado_em,
                    atualizado_em
                )
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                """,
                (
                    fase,
                    tipo,
                    chave,
                    valor,
                    origem,
                    importancia,
                    self._json(metadados or {}),
                    agora,
                    agora,
                ),
            )

        memoria = self.buscar_memoria(cursor.lastrowid)
        return memoria or {"memoria_id": cursor.lastrowid}

    def listar_memorias(
        self,
        limite: int = 20,
        fase: int | None = None,
    ) -> list[dict[str, Any]]:
        """Lista memorias ativas."""
        filtros = ["ativa = 1"]
        parametros: list[Any] = []

        if fase is not None:
            filtros.append("fase = ?")
            parametros.append(fase)

        parametros.append(limite)
        sql = f"""
            SELECT *
            FROM memorias
            WHERE {' AND '.join(filtros)}
            ORDER BY importancia DESC, atualizado_em DESC, id DESC
            LIMIT ?
        """

        with self._conectar() as conexao:
            linhas = conexao.execute(sql, parametros).fetchall()

        return [self._memoria_dict(linha) for linha in linhas]

    def buscar_memoria(self, memoria_id: int) -> dict[str, Any] | None:
        """Busca uma memoria por id."""
        with self._conectar() as conexao:
            linha = conexao.execute(
                "SELECT * FROM memorias WHERE id = ?",
                (memoria_id,),
            ).fetchone()

        return self._memoria_dict(linha) if linha else None

    def buscar_memoria_por_chave(self, chave: str) -> dict[str, Any] | None:
        """Busca memoria ativa por chave."""
        with self._conectar() as conexao:
            linha = conexao.execute(
                """
                SELECT *
                FROM memorias
                WHERE ativa = 1
                  AND chave = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (chave,),
            ).fetchone()

        return self._memoria_dict(linha) if linha else None

    def atualizar_memoria(
        self,
        memoria_id: int,
        valor: str,
        importancia: int,
        metadados: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Atualiza valor, importancia e metadados de uma memoria."""
        agora = self._agora()
        with self._conectar() as conexao:
            conexao.execute(
                """
                UPDATE memorias
                SET valor = ?,
                    importancia = ?,
                    metadados_json = ?,
                    atualizado_em = ?
                WHERE id = ?
                """,
                (
                    valor,
                    importancia,
                    self._json(metadados or {}),
                    agora,
                    memoria_id,
                ),
            )

        return self.buscar_memoria(memoria_id)

    def desativar_por_busca(self, busca: str) -> list[dict[str, Any]]:
        """Desativa memorias que contenham o texto informado."""
        agora = self._agora()
        termo = f"%{busca}%"

        with self._conectar() as conexao:
            linhas = conexao.execute(
                """
                SELECT *
                FROM memorias
                WHERE ativa = 1
                  AND (valor LIKE ? OR chave LIKE ?)
                """,
                (termo, termo),
            ).fetchall()
            ids = [linha["id"] for linha in linhas]

            if ids:
                marcadores = ",".join("?" for _ in ids)
                conexao.execute(
                    f"""
                    UPDATE memorias
                    SET ativa = 0,
                        atualizado_em = ?
                    WHERE id IN ({marcadores})
                    """,
                    [agora, *ids],
                )

        return [self._memoria_dict(linha) for linha in linhas]

    def registrar_evento(
        self,
        texto: str,
        analise: dict[str, Any] | None,
        resultado: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Registra um evento de conversa/processamento."""
        agora = self._agora()
        agente = None
        tipo_resultado = None
        dominio = None
        intencao = None

        if isinstance(resultado, dict):
            agente = resultado.get("agente")
            tipo_resultado = resultado.get("tipo")

        if isinstance(analise, dict):
            dominio = analise.get("dominio")
            intencao = analise.get("intencao")

        with self._conectar() as conexao:
            cursor = conexao.execute(
                """
                INSERT INTO memoria_eventos (
                    texto,
                    dominio,
                    intencao,
                    agente,
                    tipo_resultado,
                    analise_json,
                    resultado_json,
                    criado_em
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    texto,
                    dominio,
                    intencao,
                    agente,
                    tipo_resultado,
                    self._json(analise or {}),
                    self._json(resultado or {}),
                    agora,
                ),
            )

        return {"evento_id": cursor.lastrowid, "criado_em": agora}

    def listar_eventos(self, limite: int = 20) -> list[dict[str, Any]]:
        """Lista eventos recentes."""
        with self._conectar() as conexao:
            linhas = conexao.execute(
                """
                SELECT *
                FROM memoria_eventos
                ORDER BY id DESC
                LIMIT ?
                """,
                (limite,),
            ).fetchall()

        return [self._evento_dict(linha) for linha in linhas]

    def contar_eventos(
        self,
        dominio: str | None = None,
        intencao: str | None = None,
        agente: str | None = None,
    ) -> int:
        """Conta eventos por filtros simples."""
        filtros = []
        parametros: list[Any] = []

        if dominio is not None:
            filtros.append("dominio = ?")
            parametros.append(dominio)

        if intencao is not None:
            filtros.append("intencao = ?")
            parametros.append(intencao)

        if agente is not None:
            filtros.append("agente = ?")
            parametros.append(agente)

        where = ""
        if filtros:
            where = f"WHERE {' AND '.join(filtros)}"

        with self._conectar() as conexao:
            linha = conexao.execute(
                f"SELECT COUNT(*) AS total FROM memoria_eventos {where}",
                parametros,
            ).fetchone()

        return int(linha["total"] or 0)

    def _inicializar(self) -> None:
        with self._conectar() as conexao:
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS memorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fase INTEGER NOT NULL,
                    tipo TEXT NOT NULL,
                    chave TEXT NOT NULL,
                    valor TEXT NOT NULL,
                    origem TEXT NOT NULL,
                    importancia INTEGER NOT NULL DEFAULT 1,
                    ativa INTEGER NOT NULL DEFAULT 1,
                    metadados_json TEXT,
                    criado_em TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL
                )
                """
            )
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS memoria_eventos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    texto TEXT NOT NULL,
                    dominio TEXT,
                    intencao TEXT,
                    agente TEXT,
                    tipo_resultado TEXT,
                    analise_json TEXT,
                    resultado_json TEXT,
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

    def _memoria_dict(self, linha: sqlite3.Row) -> dict[str, Any]:
        return {
            "tipo_resultado": "memoria",
            "memoria_id": linha["id"],
            "fase": linha["fase"],
            "tipo_memoria": linha["tipo"],
            "chave": linha["chave"],
            "valor": linha["valor"],
            "origem": linha["origem"],
            "importancia": linha["importancia"],
            "ativa": bool(linha["ativa"]),
            "metadados": self._from_json(linha["metadados_json"]),
            "criado_em": linha["criado_em"],
            "atualizado_em": linha["atualizado_em"],
        }

    def _evento_dict(self, linha: sqlite3.Row) -> dict[str, Any]:
        return {
            "evento_id": linha["id"],
            "texto": linha["texto"],
            "dominio": linha["dominio"],
            "intencao": linha["intencao"],
            "agente": linha["agente"],
            "tipo_resultado": linha["tipo_resultado"],
            "criado_em": linha["criado_em"],
        }

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
