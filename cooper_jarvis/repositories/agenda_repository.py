"""Repositorio JSON para tarefas e logs da agenda."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from repositories.base_repository import BaseRepository


class AgendaRepository(BaseRepository):
    """Salva e recupera tarefas e logs da agenda."""

    def __init__(
        self,
        caminho_tarefas: str | Path | None = None,
        caminho_logs: str | Path | None = None,
    ) -> None:
        data_dir = Path(__file__).resolve().parents[1] / "data"
        self.caminho_tarefas = Path(caminho_tarefas or data_dir / "agenda.json")
        self.caminho_logs = Path(caminho_logs or data_dir / "agenda_logs.json")
        self.caminho_tarefas.parent.mkdir(parents=True, exist_ok=True)
        self.caminho_logs.parent.mkdir(parents=True, exist_ok=True)

    def salvar_tarefas(
        self,
        tarefas: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Persiste a lista de tarefas no JSON."""
        self.caminho_tarefas.write_text(
            json.dumps(tarefas, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return tarefas

    def recuperar_tarefas(self) -> list[dict[str, Any]]:
        """Recupera a lista de tarefas salva."""
        return self._recuperar_lista(self.caminho_tarefas)

    def registrar_log(self, log: dict[str, Any]) -> dict[str, Any]:
        """Adiciona um log da agenda no JSON."""
        logs = self.recuperar_logs()
        logs.append(log)
        self.caminho_logs.write_text(
            json.dumps(logs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return log

    def recuperar_logs(self) -> list[dict[str, Any]]:
        """Recupera os logs salvos da agenda."""
        return self._recuperar_lista(self.caminho_logs)

    def _recuperar_lista(self, caminho: Path) -> list[dict[str, Any]]:
        if not caminho.exists():
            return []

        conteudo = caminho.read_text(encoding="utf-8").strip()
        if not conteudo:
            return []

        try:
            dados = json.loads(conteudo)
        except json.JSONDecodeError:
            return []

        return dados if isinstance(dados, list) else []
