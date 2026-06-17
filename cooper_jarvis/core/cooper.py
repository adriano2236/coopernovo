"""Orquestrador central do Cooper Jarvis."""

from typing import Any

from core.response_builder import ResponseBuilder
from core.router import Router
from nlp.interpretador import Interpretador


class Cooper:
    """Coordena interpretador, router e formatador de respostas."""

    def __init__(
        self,
        interpretador: Interpretador,
        router: Router,
        response_builder: ResponseBuilder,
        contexto_agent: Any | None = None,
        historico_agent: Any | None = None,
    ) -> None:
        self.interpretador = interpretador
        self.router = router
        self.response_builder = response_builder
        self.contexto_agent = contexto_agent
        self.historico_agent = historico_agent

    def responder(self, texto: str) -> str:
        """Processa texto de entrada e devolve resposta formatada."""
        analise: dict[str, Any] = self.interpretador.interpretar(texto)
        resultado = self.router.rotear(analise)
        resposta = self.response_builder.formatar(resultado)
        self._registrar_contexto(analise, resultado, resposta)
        self._registrar_historico(analise, resultado, resposta)
        return resposta

    def _registrar_contexto(
        self,
        analise: dict[str, Any],
        resultado: dict[str, Any],
        resposta: str,
    ) -> None:
        """Orquestra o registro do contexto imediato."""
        if self.contexto_agent is None:
            return

        self.contexto_agent.registrar_interacao(
            analise=analise,
            resultado=resultado,
            resposta=resposta,
        )

    def _registrar_historico(
        self,
        analise: dict[str, Any],
        resultado: dict[str, Any],
        resposta: str,
    ) -> None:
        """Orquestra o registro do historico de conversa."""
        if self.historico_agent is None:
            return

        self.historico_agent.registrar_interacao(
            analise=analise,
            resultado=resultado,
            resposta=resposta,
        )
