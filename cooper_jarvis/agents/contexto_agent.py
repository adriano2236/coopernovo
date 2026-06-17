"""Agente da memoria de contexto imediato."""

from typing import Any

from agents.base_agent import BaseAgent
from repositories.contexto_repository import ContextoRepository


class ContextoAgent(BaseAgent):
    """Gerencia o contexto imediato do Cooper Jarvis."""

    nome = "contexto"

    def __init__(self, repository: ContextoRepository | None = None) -> None:
        self.repository = repository or ContextoRepository()

    def pode_processar(self, analise: dict[str, Any]) -> bool:
        """Identifica consultas sobre o contexto imediato."""
        return analise.get("intencao") == "contexto_consultar"

    def processar(self, analise: dict[str, Any]) -> dict[str, Any]:
        """Recupera o contexto imediato salvo."""
        contexto = self.recuperar_contexto()
        return {
            "agent": self.nome,
            "tipo": "contexto",
            "dados": {
                "mensagem": self._montar_resposta(contexto),
                "contexto": contexto,
            },
        }

    def registrar_interacao(
        self,
        analise: dict[str, Any],
        resultado: dict[str, Any],
        resposta: str,
    ) -> dict[str, Any]:
        """Decide quais dados da interacao devem virar contexto imediato."""
        contexto = {
            "ultimo_comando": analise.get("texto_original") or "",
            "ultima_resposta": resposta,
            "ultimo_agente": resultado.get("agent") or "",
        }
        return self.repository.salvar(contexto)

    def recuperar_contexto(self) -> dict[str, Any]:
        """Recupera o contexto imediato atual."""
        return self.repository.recuperar()

    def _montar_resposta(self, contexto: dict[str, Any]) -> str:
        if not contexto:
            return "Ainda nao existe contexto imediato salvo."

        return (
            "Contexto imediato:\n"
            f"- ultimo comando: {contexto.get('ultimo_comando') or 'nenhum'}\n"
            f"- ultima resposta: {contexto.get('ultima_resposta') or 'nenhuma'}\n"
            f"- ultimo agente: {contexto.get('ultimo_agente') or 'nenhum'}"
        )
