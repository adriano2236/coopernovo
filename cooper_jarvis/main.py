"""Ponto de entrada inicial do Cooper Jarvis."""

from agents.assistente_agent import AssistenteAgent
from core.cooper import Cooper
from core.response_builder import ResponseBuilder
from core.router import Router
from nlp.interpretador import Interpretador


def criar_cooper() -> Cooper:
    """Monta a fundacao inicial do Cooper Jarvis."""
    return Cooper(
        interpretador=Interpretador(),
        router=Router(agents=[AssistenteAgent()]),
        response_builder=ResponseBuilder(),
    )


def main() -> None:
    """Executa um teste minimo da fundacao."""
    cooper = criar_cooper()
    resposta = cooper.responder("oi")
    print(resposta)


if __name__ == "__main__":
    main()
