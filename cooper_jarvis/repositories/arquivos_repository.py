"""Repositorio JSON para logs e listagens de arquivos."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from repositories.base_repository import BaseRepository


class ArquivosRepository(BaseRepository):
    """Registra logs e lista dados simples de pastas locais."""

    def __init__(self, caminho_log: str | Path | None = None) -> None:
        data_dir = Path(__file__).resolve().parents[1] / "data"
        self.caminho_log = Path(caminho_log or data_dir / "arquivos_logs.json")
        self.caminho_log.parent.mkdir(parents=True, exist_ok=True)

    def registrar(self, log: dict[str, Any]) -> dict[str, Any]:
        """Adiciona um log de acao em arquivo JSON."""
        logs = self.recuperar_logs()
        logs.append(log)
        self.caminho_log.write_text(
            json.dumps(logs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return log

    def recuperar_logs(self) -> list[dict[str, Any]]:
        """Recupera logs de acoes de arquivos."""
        if not self.caminho_log.exists():
            return []

        conteudo = self.caminho_log.read_text(encoding="utf-8").strip()
        if not conteudo:
            return []

        try:
            dados = json.loads(conteudo)
        except json.JSONDecodeError:
            return []

        return dados if isinstance(dados, list) else []

    def listar(self, caminho: str | Path, limite: int = 30) -> list[dict[str, Any]]:
        """Lista itens diretos de uma pasta."""
        pasta = Path(caminho)
        if not pasta.exists() or not pasta.is_dir():
            return []

        itens = []
        for item in sorted(pasta.iterdir(), key=lambda valor: valor.name.lower()):
            itens.append(
                {
                    "nome": item.name,
                    "caminho": str(item),
                    "tipo": "pasta" if item.is_dir() else "arquivo",
                }
            )
            if len(itens) >= limite:
                break

        return itens
