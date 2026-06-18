"""Repositorio JSON para logs de acoes do sistema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from repositories.base_repository import BaseRepository


class SistemaRepository(BaseRepository):
    """Salva e recupera logs de acoes executadas."""

    def __init__(self, caminho: str | Path | None = None) -> None:
        data_dir = Path(__file__).resolve().parents[1] / "data"
        self.caminho = Path(caminho or data_dir / "sistema_logs.json")
        self.caminho.parent.mkdir(parents=True, exist_ok=True)

    def registrar(self, log: dict[str, Any]) -> dict[str, Any]:
        """Adiciona um log ao arquivo JSON."""
        logs = self.recuperar()
        logs.append(log)
        self.caminho.write_text(
            json.dumps(logs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return log

    def recuperar(self) -> list[dict[str, Any]]:
        """Recupera os logs salvos."""
        if not self.caminho.exists():
            return []

        conteudo = self.caminho.read_text(encoding="utf-8").strip()
        if not conteudo:
            return []

        try:
            dados = json.loads(conteudo)
        except json.JSONDecodeError:
            return []

        return dados if isinstance(dados, list) else []
