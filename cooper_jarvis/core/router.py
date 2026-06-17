"""Roteador de agentes do Cooper Jarvis."""

from typing import Any

from agents.base_agent import BaseAgent


class Router:
    """Escolhe qual agente deve processar uma analise."""

    def __init__(self, agents: list[BaseAgent] | None = None) -> None:
        self.agents = agents or []

    def rotear(self, analise: dict[str, Any]) -> dict[str, Any]:
        """Envia a analise para o primeiro agente compativel."""
        for agent in self.agents:
            if agent.pode_processar(analise):
                return agent.processar(analise)

        return {
            "agent": "router",
            "tipo": "nao_processado",
            "dados": {
                "mensagem": "Nenhum agente disponivel para esta solicitacao.",
            },
        }
