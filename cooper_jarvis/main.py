"""Ponto de entrada inicial do Cooper Jarvis."""

from agents.assistente_agent import AssistenteAgent
from agents.contexto_agent import ContextoAgent
from core.cooper import Cooper
from core.response_builder import ResponseBuilder
from core.router import Router
from nlp.interpretador import Interpretador
from repositories.contexto_repository import ContextoRepository


def criar_cooper() -> Cooper:
    """Monta a fundacao inicial do Cooper Jarvis."""
    contexto_repository = ContextoRepository()
    contexto_agent = ContextoAgent(repository=contexto_repository)

    return Cooper(
        interpretador=Interpretador(),
        router=Router(agents=[contexto_agent, AssistenteAgent()]),
        response_builder=ResponseBuilder(),
        contexto_agent=contexto_agent,
    )


def main() -> None:
    """Executa um teste minimo da fundacao."""
    cooper = criar_cooper()
    resposta = cooper.responder("oi")
    print(resposta)


if __name__ == "__main__":
    main()
