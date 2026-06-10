"""
Contrato base dos agentes do Cooper.

Este módulo define a classe abstrata BaseAgent, que deve ser herdada por
qualquer agente especializado do sistema, como VendasAgent, ComprasAgent ou
EstoqueAgent.

Regra arquitetural principal:
    Agents = DATA ONLY

Ou seja, agentes não devem imprimir mensagens diretamente, interagir com o
usuário, formatar respostas finais ou controlar fluxo global da aplicação.
Eles apenas analisam uma mensagem e retornam um dicionário padronizado para
que outras camadas do Cooper decidam como responder.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """
    Classe mãe de todos os agentes do Cooper.

    Todo agente especializado deve implementar dois métodos obrigatórios:
    `pode_processar` e `processar`.

    O método `pode_processar` informa se o agente é capaz de lidar com uma
    mensagem. O método `processar` executa a lógica do agente e deve retornar
    sempre um dicionário no formato padrão do Cooper.
    """

    def __init__(self, nome: str) -> None:
        """
        Inicializa um agente com um nome identificador.

        Args:
            nome: Nome legível do agente, usado para identificação interna.
        """
        self.nome = nome

    @abstractmethod
    def pode_processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None
    ) -> bool:
        """
        Indica se o agente consegue processar a mensagem recebida.

        Args:
            msg: Mensagem original enviada ao Cooper.
            analise: Resultado opcional da camada de NLP/interpretação.
        Returns:
            True se o agente puder processar a mensagem; caso contrário, False.
        """
        pass

    @abstractmethod
    def processar(self, msg: str, analise: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Processa a mensagem e retorna dados estruturados.

        Este método nunca deve imprimir, renderizar ou enviar uma resposta
        diretamente ao usuário. A responsabilidade do agente é apenas produzir
        dados no formato padrão do Cooper.

        Args:
            msg: Mensagem original enviada ao Cooper.
            analise: Resultado opcional da camada de NLP/interpretação.

        Returns:
            Um dicionário padronizado contendo os dados produzidos pelo agente.
        """
        pass

    def resposta_padrao(
        self,
        status: str,
        tipo: str,
        dados: dict[str, Any] | None = None,
        erro: str | None = None,
    ) -> dict[str, Any]:

        return {
            "agente": self.nome,
            "status": status,
            "tipo": tipo,
            "dados": dados or {},
            "erro": erro,
        }
        
    def __repr__(self) -> str:
        """Retorna uma representação simples do agente para depuração."""
        return f"{self.__class__.__name__}(nome={self.nome!r})"
