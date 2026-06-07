"""
Contrato base dos agentes do Cooper.

Todos os agentes especializados (VendasAgent, ComprasAgent,
EstoqueAgent, etc.) devem herdar desta classe.

Princípio arquitetural:

    Agents = DATA ONLY

Os agentes são responsáveis apenas pela lógica de negócio e pelo
retorno de dados estruturados.

Eles NÃO devem:
- imprimir mensagens;
- formatar respostas;
- conversar diretamente com o usuário;
- controlar fluxo do sistema.

A responsabilidade de transformar esses dados em linguagem natural
pertence exclusivamente ao ResponseBuilder.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """
    Classe base de todos os agentes do Cooper.
    """

    def __init__(self, nome: str):
        self.nome = nome

    @abstractmethod
    def pode_processar(self, msg: str) -> bool:
        """
        Informa se este agente consegue tratar a mensagem.
        """
        raise NotImplementedError

    @abstractmethod
    def processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Executa a lógica do agente.

        Deve SEMPRE retornar um dicionário seguindo o contrato
        oficial do Cooper.
        """
        raise NotImplementedError

    def resposta_padrao(
        self,
        *,
        status: str,
        tipo: str,
        dados: dict[str, Any] | None = None,
        erro: str | None = None,
    ) -> dict[str, Any]:
        """
        Cria um retorno padronizado para qualquer agente.

        Estrutura oficial:

        {
            "agente": "...",
            "status": "ok" | "erro",
            "tipo": "...",
            "dados": {},
            "erro": None | "codigo_do_erro"
        }
        """

        return {
            "agente": self.nome,
            "status": status,
            "tipo": tipo,
            "dados": dados or {},
            "erro": erro,
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(nome={self.nome!r})"
