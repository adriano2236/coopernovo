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
    ) -> None:
        self.interpretador = interpretador
        self.router = router
        self.response_builder = response_builder

    def responder(self, texto: str) -> str:
        """Processa texto de entrada e devolve resposta formatada."""
        analise: dict[str, Any] = self.interpretador.interpretar(texto)
        resultado = self.router.rotear(analise)
        return self.response_builder.formatar(resultado)
