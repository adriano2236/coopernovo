"""Acesso SQLite para backup e exportacao de dados do Cooper."""

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any, Iterator


class BackupRepository:
    """Repositorio para leitura e copia segura do banco SQLite."""

    def __init__(self, db_path: str | Path = "data/cooper.db") -> None:
        self.db_path = Path(db_path)

    def banco_existe(self) -> bool:
        """Indica se o banco principal existe."""
        return self.db_path.exists() and self.db_path.is_file()

    def criar_backup_sqlite(self, destino: str | Path) -> dict[str, Any]:
        """Cria uma copia consistente do banco usando a API de backup do SQLite."""
        destino_path = Path(destino)
        if not self.banco_existe():
            return {
                "tipo_resultado": "backup_nao_encontrado",
                "origem": str(self.db_path),
            }

        destino_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as origem:
            with sqlite3.connect(destino_path) as copia:
                origem.backup(copia)

        return {
            "tipo_resultado": "backup_arquivo",
            "origem": str(self.db_path),
            "caminho": str(destino_path),
            "tamanho_bytes": destino_path.stat().st_size,
            "criado_em": self._agora(),
        }

    def exportar_snapshot(self) -> dict[str, Any]:
        """Le todas as tabelas do banco para exportacao externa."""
        if not self.banco_existe():
            return {
                "tipo_resultado": "backup_nao_encontrado",
                "origem": str(self.db_path),
            }

        with self._conectar() as conexao:
            tabelas = self._listar_tabelas(conexao)
            itens = []
            total_registros = 0
            for tabela in tabelas:
                colunas = self._listar_colunas(conexao, tabela)
                registros = self._listar_registros(conexao, tabela)
                total_registros += len(registros)
                itens.append(
                    {
                        "nome": tabela,
                        "colunas": colunas,
                        "total_registros": len(registros),
                        "registros": registros,
                    }
                )

        return {
            "tipo_resultado": "backup_snapshot",
            "origem": str(self.db_path),
            "gerado_em": self._agora(),
            "total_tabelas": len(itens),
            "total_registros": total_registros,
            "tabelas": itens,
        }

    @contextmanager
    def _conectar(self) -> Iterator[sqlite3.Connection]:
        conexao = sqlite3.connect(self.db_path)
        conexao.row_factory = sqlite3.Row
        try:
            yield conexao
        finally:
            conexao.close()

    def _listar_tabelas(self, conexao: sqlite3.Connection) -> list[str]:
        linhas = conexao.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()
        return [str(linha["name"]) for linha in linhas]

    def _listar_colunas(
        self,
        conexao: sqlite3.Connection,
        tabela: str,
    ) -> list[str]:
        linhas = conexao.execute(
            f"PRAGMA table_info({self._identificador(tabela)})"
        ).fetchall()
        return [str(linha["name"]) for linha in linhas]

    def _listar_registros(
        self,
        conexao: sqlite3.Connection,
        tabela: str,
    ) -> list[dict[str, Any]]:
        linhas = conexao.execute(
            f"SELECT * FROM {self._identificador(tabela)}"
        ).fetchall()
        return [dict(linha) for linha in linhas]

    def _identificador(self, nome: str) -> str:
        return '"' + str(nome).replace('"', '""') + '"'

    def _agora(self) -> str:
        return datetime.now(timezone.utc).isoformat()
