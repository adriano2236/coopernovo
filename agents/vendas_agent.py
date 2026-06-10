"""
Agente de vendas do Cooper.

Este módulo define o VendasAgent, responsável por reconhecer e processar
mensagens relacionadas a vendas. O agente segue o contrato definido por
BaseAgent e retorna apenas dados estruturados.

Regra arquitetural principal:
    VendasAgent = lógica de domínio de vendas em formato DATA ONLY
"""

from typing import Any

from agents.base_agent import BaseAgent


class VendasAgent(BaseAgent):
    """
    Agente especializado em solicitações de vendas.

    Este agente identifica intenções ligadas a vendas, pedidos, clientes,
    faturamento, orçamento e registro de venda. A implementação inicial é
    propositalmente conservadora para servir como base estável antes da adição
    de regras mais específicas.
    """

    PALAVRAS_CHAVE = {
        "venda",
        "vendas",
        "vender",
        "vendido",
        "pedido",
        "pedidos",
        "cliente",
        "clientes",
        "orçamento",
        "orcamento",
        "faturamento",
        "nota",
        "receita",
    }

    def __init__(self) -> None:
        """Inicializa o agente de vendas com seu nome padrão."""
        super().__init__(nome="vendas")

    def pode_processar(
            self,
            msg: str,
            analise: dict[str, Any] | None = None
        ) -> bool:

        if analise and analise.get("dominio") == "vendas":
            return True

        texto = (msg or "").lower()
        return any(palavra in texto for palavra in self.PALAVRAS_CHAVE)

    def processar(self, msg: str, analise: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Processa uma solicitação relacionada a vendas.

        Args:
            msg: Mensagem original enviada ao Cooper.
            analise: Resultado opcional da camada de NLP/interpretação.

        Returns:
            Dicionário padronizado contendo os dados produzidos pelo agente.
        """
        intencao = self._definir_intencao(msg, analise=analise)

        return self.resposta_padrao(
            status="sucesso",
            tipo=intencao,
            dados={
                "mensagem_original": msg,
                "analise": analise or {},
            },
        )

    def _definir_intencao(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> str:
        """
        Define uma intenção inicial para o domínio de vendas.

        Args:
            msg: Mensagem original enviada ao Cooper.
            analise: Resultado opcional da camada NLP.

        Returns:
            Nome da intenção de vendas identificada.
        """
        if analise and analise.get("intencao"):
            return str(analise["intencao"])

        texto = (msg or "").lower()

        if "orçamento" in texto or "orcamento" in texto:
            return "vendas_orcamento"

        if "pedido" in texto:
            return "vendas_pedido"

        if "cliente" in texto:
            return "vendas_cliente"

        if "faturamento" in texto or "receita" in texto:
            return "vendas_faturamento"

        return "vendas_geral"
