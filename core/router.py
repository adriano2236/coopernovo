"""
Roteador central do Cooper.

Este módulo define a classe Router, responsável por escolher qual agente deve
processar uma mensagem recebida. O Router não executa regra de negócio própria,
não formata respostas finais e não conversa diretamente com o usuário.

Regra arquitetural principal:
    Router = seleção e delegação

A responsabilidade do Router é percorrer os agentes registrados, identificar o
primeiro agente capaz de processar a mensagem e delegar o processamento a ele.
"""

from typing import Any

from agents.base_agent import BaseAgent


class Router:
    """
    Coordena a escolha do agente apropriado para uma mensagem.

    O Router recebe uma lista de agentes especializados e consulta cada um por
    meio do método `pode_processar`. Quando encontra um agente compatível,
    chama o método `processar` desse agente e retorna o dicionário produzido.
    """

    def __init__(self, agents: list[BaseAgent] | None = None) -> None:
        """
        Inicializa o roteador com uma lista opcional de agentes.

        Args:
            agents: Lista de agentes disponíveis para roteamento.
        """
        self.agents = agents or []

    def registrar(self, agent: BaseAgent) -> None:
        """
        Registra um novo agente no roteador.

        Args:
            agent: Instância de um agente que herda de BaseAgent.
        """
        if not isinstance(agent, BaseAgent):
            raise TypeError("O agente registrado deve herdar de BaseAgent.")

        self.agents.append(agent)

    def rotear(self, msg: str, analise: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Encaminha uma mensagem para o primeiro agente capaz de processá-la.

        Args:
            msg: Mensagem original enviada ao Cooper.
            analise: Resultado opcional da camada de NLP/interpretação.

        Returns:
            Dicionário padronizado retornado pelo agente selecionado ou uma
            resposta de fallback quando nenhum agente for compatível.
        """
        mensagem = (msg or "").strip()

        if not mensagem:
            return self._resposta_fallback(
                status="erro",
                mensagem="Mensagem vazia recebida pelo roteador.",
                erro="mensagem_vazia",
            )

        for agent in self.agents:
            if agent.pode_processar(mensagem, analise):
                return agent.processar(mensagem, analise=analise)

        return self._resposta_fallback(
            status="nao_processado",
            mensagem="Nenhum agente disponível conseguiu processar a mensagem.",
            erro=None,
        )

    def listar_agents(self) -> list[str]:
        """
        Lista os nomes dos agentes registrados.

        Returns:
            Lista com os nomes identificadores dos agentes disponíveis.
        """
        return [agent.nome for agent in self.agents]

    def _resposta_fallback(
        self,
        status: str,
        mensagem: str,
        erro: str | None = None,
    ) -> dict[str, Any]:
        """
        Cria uma resposta interna quando não há agente apto a processar.

        Args:
            status: Estado do roteamento.
            mensagem: Mensagem interna explicativa.
            erro: Código ou descrição opcional do erro.

        Returns:
            Dicionário no formato padrão mínimo do Cooper.
        """
        return {
            "agente": "router",
            "status": status,
            "tipo": "fallback",
            "dados": {
                "mensagem": mensagem
            },
            "erro": erro,
        }

    def __repr__(self) -> str:
        """Retorna uma representação simples do roteador para depuração."""
        return f"Router(agents={self.listar_agents()!r})"
