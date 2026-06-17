"""Agente minimo de conversa inicial."""

from typing import Any

from agents.base_agent import BaseAgent


class AssistenteAgent(BaseAgent):
    """Agente inicial apenas para validar a fundacao."""

    nome = "assistente"

    def pode_processar(self, analise: dict[str, Any]) -> bool:
        """Aceita mensagens gerais enquanto nao existem agentes especializados."""
        return analise.get("intencao") == "conversa"

    def processar(self, analise: dict[str, Any]) -> dict[str, Any]:
        """Retorna uma resposta minima de fundacao."""
        return {
            "agent": self.nome,
            "tipo": "conversa",
            "dados": {
                "mensagem": "Cooper Jarvis iniciado. Fundacao pronta.",
            },
        }
