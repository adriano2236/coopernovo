"""Contrato base dos agentes."""

from typing import Any


class BaseAgent:
    """Classe base para agentes de logica."""

    nome = "base"

    def pode_processar(self, analise: dict[str, Any]) -> bool:
        """Indica se o agente consegue processar a analise."""
        raise NotImplementedError

    def processar(self, analise: dict[str, Any]) -> dict[str, Any]:
        """Executa a logica do agente."""
        raise NotImplementedError
