"""
Ponto de entrada simples do Cooper.

Este arquivo demonstra como montar o Cooper com seus agentes principais,
interpretador NLP, roteador e construtor de respostas. Ele pode ser expandido
posteriormente para interface CLI, API, desktop ou web.
"""

from agents.compras_agent import ComprasAgent
from agents.estoque_agent import EstoqueAgent
from agents.vendas_agent import VendasAgent
from core.cooper import Cooper
from core.response_builder import ResponseBuilder
from core.router import Router
from nlp.interpretador import Interpretador


def criar_cooper() -> Cooper:
    """
    Cria uma instância padrão do Cooper com os agentes principais.

    Returns:
        Instância configurada do Cooper.
    """
    router = Router(
        agents=[
            VendasAgent(),
            ComprasAgent(),
            EstoqueAgent(),
        ]
    )

    return Cooper(
        router=router,
        response_builder=ResponseBuilder(),
        interpretador=Interpretador(),
    )


def main() -> None:
    """Executa uma interface de linha de comando simples para testes locais."""
    cooper = criar_cooper()

    print("Cooper iniciado. Digite 'sair' para encerrar.")

    while True:
        msg = input("Você: ").strip()

        if msg.lower() in {"sair", "exit", "quit"}:
            print("Cooper encerrado.")
            break
        
        resposta = cooper.responder(msg)
        print(f"Cooper: {resposta}")


if __name__ == "__main__":
    main()
