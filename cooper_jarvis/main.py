"""Ponto de entrada inicial do Cooper Jarvis."""

from agents.assistente_agent import AssistenteAgent
from agents.contexto_agent import ContextoAgent
from agents.historico_agent import HistoricoAgent
from agents.memoria_operacional_agent import MemoriaOperacionalAgent
from core.cooper import Cooper
from core.response_builder import ResponseBuilder
from core.router import Router
from nlp.interpretador import Interpretador
from repositories.contexto_repository import ContextoRepository
from repositories.historico_repository import HistoricoRepository
from repositories.memoria_operacional_repository import MemoriaOperacionalRepository


COMANDOS_SAIDA = {"sair", "exit", "quit"}


def criar_cooper() -> Cooper:
    """Monta a fundacao inicial do Cooper Jarvis."""
    contexto_repository = ContextoRepository()
    contexto_agent = ContextoAgent(repository=contexto_repository)
    historico_repository = HistoricoRepository()
    historico_agent = HistoricoAgent(repository=historico_repository)
    memoria_operacional_repository = MemoriaOperacionalRepository()
    memoria_operacional_agent = MemoriaOperacionalAgent(
        repository=memoria_operacional_repository
    )

    return Cooper(
        interpretador=Interpretador(),
        router=Router(
            agents=[
                contexto_agent,
                historico_agent,
                memoria_operacional_agent,
                AssistenteAgent(),
            ]
        ),
        response_builder=ResponseBuilder(),
        contexto_agent=contexto_agent,
        historico_agent=historico_agent,
    )


def exibir_ajuda() -> None:
    """Mostra comandos basicos da CLI."""
    print("Comandos:")
    print("  ajuda   Mostra esta ajuda.")
    print("  sair    Encerra o Cooper Jarvis.")
    print("")
    print("Exemplos:")
    print("  meu nome e Adriano")
    print("  meu projeto principal e Cooper Jarvis")
    print("  prefiro respostas diretas")
    print("  o que voce sabe sobre mim")
    print("  mostrar historico")
    print("  qual foi o ultimo comando?")


def main() -> None:
    """Executa a conversa no terminal."""
    cooper = criar_cooper()

    print("Cooper Jarvis iniciado. Digite 'sair' para encerrar.")
    print("Digite 'ajuda' para ver exemplos.")

    while True:
        try:
            mensagem = input("Voce: ").strip()
        except KeyboardInterrupt:
            print("\nCooper Jarvis encerrado.")
            break

        comando = mensagem.lower()
        if comando in COMANDOS_SAIDA:
            print("Cooper Jarvis encerrado.")
            break

        if not mensagem:
            print("Cooper: Envie uma mensagem para eu analisar.")
            continue

        if comando in {"ajuda", "help", "?"}:
            exibir_ajuda()
            continue

        print(f"Cooper: {cooper.responder(mensagem)}")


if __name__ == "__main__":
    main()
