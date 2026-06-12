"""
Núcleo principal do Cooper.

Este módulo define a classe Cooper, responsável por orquestrar o fluxo central
da aplicação. O Cooper recebe uma mensagem, solicita uma análise opcional ao
interpretador NLP, envia a mensagem ao Router e utiliza o ResponseBuilder para
produzir a resposta final.

Regra arquitetural principal:
    Cooper = orquestração

O núcleo não deve concentrar regras específicas de vendas, compras ou estoque.
Essas responsabilidades pertencem aos agentes especializados.
"""

from typing import Any
from agents.base_agent import BaseAgent
from core.response_builder import ResponseBuilder
from core.router import Router


class Cooper:
    """
    Orquestrador principal do sistema Cooper.

    Esta classe conecta as camadas centrais do projeto sem assumir a lógica de
    negócio de cada domínio. Ela mantém o fluxo previsível e facilita a adição
    de novos agentes no futuro.
    """

    def __init__(
        self,
        router: Router,
        response_builder: ResponseBuilder | None = None,
        interpretador: Any | None = None,
        memoria_repository: Any | None = None,
        memoria_agent: Any | None = None,
    ) -> None:
        """
        Inicializa o Cooper com suas dependências principais.

        Args:
            router: Roteador responsável por selecionar o agente apropriado.
            response_builder: Construtor de respostas finais. Quando não for
                informado, uma instância padrão será criada.
            interpretador: Camada opcional de NLP para análise prévia da
                mensagem.
        """
        if not isinstance(router, Router):
            raise TypeError("router deve ser uma instância de Router.")

        self.router = router
        self.response_builder = response_builder or ResponseBuilder()
        self.interpretador = interpretador
        self.memoria_repository = memoria_repository
        self.memoria_agent = memoria_agent

    def responder(self, msg: str) -> str:
        """
        Processa uma mensagem e retorna a resposta final ao usuário.

        Args:
            msg: Mensagem original enviada ao Cooper.

        Returns:
            Texto final construído pelo ResponseBuilder.
        """
        resultado = self.processar(msg)

        if not isinstance(resultado, dict):
            return "Erro interno do Cooper."
        
        return self.response_builder.construir(resultado)

    def processar(self, msg: str) -> dict[str, Any]:
        """
        Executa o fluxo interno completo sem formatar a resposta final.

        Este método é útil para testes, depuração e interfaces que desejam
        receber os dados internos padronizados em vez de texto pronto.

        Args:
            msg: Mensagem original enviada ao Cooper.

        Returns:
            Dicionário padronizado retornado pelo Router ou pelo agente.
        """
        analise = self._analisar(msg)
        resultado = self.router.rotear(msg, analise=analise)
        self._registrar_evento_memoria(msg, analise, resultado)
        return resultado

    def _analisar(self, msg: str) -> dict[str, Any] | None:
        """
        Executa a análise NLP quando um interpretador estiver configurado.

        Args:
            msg: Mensagem original enviada ao Cooper.

        Returns:
            Dicionário de análise NLP ou None quando não houver interpretador.
        """
        if self.interpretador is None:
            return None

        if hasattr(self.interpretador, "interpretar"):
            return self.interpretador.interpretar(msg)

        if callable(self.interpretador):
            return self.interpretador(msg)

        raise TypeError(
            "interpretador deve ser callable ou possuir um método interpretar(msg)."
        )

    def _registrar_evento_memoria(
        self,
        msg: str,
        analise: dict[str, Any] | None,
        resultado: dict[str, Any] | None,
    ) -> None:
        """Registra historico de conversa quando a memoria estiver configurada."""
        if self.memoria_repository is None:
            return

        if not hasattr(self.memoria_repository, "registrar_evento"):
            return

        try:
            self.memoria_repository.registrar_evento(
                texto=msg,
                analise=analise,
                resultado=resultado,
            )
        except Exception:
            return

        if self.memoria_agent is None:
            return

        if not hasattr(self.memoria_agent, "aprender_com_evento"):
            return

        try:
            self.memoria_agent.aprender_com_evento(
                texto=msg,
                analise=analise,
                resultado=resultado,
            )
        except Exception:
            return

    def registrar_agent(self, agent: BaseAgent) -> None:
        """
        Registra um agente no Router interno.

        Args:
            agent: Agente especializado que herda de BaseAgent.
        """
        self.router.registrar(agent)

    def listar_agents(self) -> list[str]:
        """
        Lista os agentes disponíveis no Router interno.

        Returns:
            Lista de nomes dos agentes registrados.
        """
        return self.router.listar_agents()

    def __repr__(self) -> str:
        """Retorna uma representação simples do Cooper para depuração."""
        return f"Cooper(agents={self.listar_agents()!r})"
