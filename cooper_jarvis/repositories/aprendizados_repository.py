"""Repositorio JSON da memoria de aprendizados."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from repositories.base_repository import BaseRepository


class AprendizadosRepository(BaseRepository):
    """Salva e recupera aprendizados em arquivo JSON."""

    def __init__(self, caminho: str | Path | None = None) -> None:
        data_dir = Path(__file__).resolve().parents[1] / "data"
        self.caminho = Path(caminho or data_dir / "aprendizados.json")
        self.caminho.parent.mkdir(parents=True, exist_ok=True)

    def salvar(self, aprendizados: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Persiste a lista de aprendizados no JSON."""
        self.caminho.write_text(
            json.dumps(aprendizados, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return aprendizados

    def recuperar(self) -> list[dict[str, Any]]:
        """Recupera a lista de aprendizados salva."""
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
