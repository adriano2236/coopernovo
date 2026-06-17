"""Repositorio JSON da memoria de contexto imediato."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from repositories.base_repository import BaseRepository


class ContextoRepository(BaseRepository):
    """Salva e recupera o contexto imediato em arquivo JSON."""

    def __init__(self, caminho: str | Path | None = None) -> None:
        data_dir = Path(__file__).resolve().parents[1] / "data"
        self.caminho = Path(caminho or data_dir / "contexto.json")
        self.caminho.parent.mkdir(parents=True, exist_ok=True)

    def salvar(self, dados: dict[str, Any]) -> dict[str, Any]:
        """Persiste dados de contexto no JSON."""
        self.caminho.write_text(
            json.dumps(dados, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return dados

    def recuperar(self) -> dict[str, Any]:
        """Recupera dados de contexto salvos."""
        if not self.caminho.exists():
            return {}

        conteudo = self.caminho.read_text(encoding="utf-8").strip()
        if not conteudo:
            return {}

        try:
            dados = json.loads(conteudo)
        except json.JSONDecodeError:
            return {}

        return dados if isinstance(dados, dict) else {}
