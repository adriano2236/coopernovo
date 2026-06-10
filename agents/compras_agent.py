"""
Agente de compras do Cooper.

Este módulo define o ComprasAgent, responsável por reconhecer e processar
mensagens relacionadas a compras, fornecedores, cotações e reposição. O agente
segue o contrato definido por BaseAgent e retorna apenas dados estruturados.

Regra arquitetural principal:
    ComprasAgent = lógica de domínio de compras em formato DATA ONLY
"""

from typing import Any

from agents.base_agent import BaseAgent


class ComprasAgent(BaseAgent):
    """
    Agente especializado em solicitações de compras.

    Este agente identifica intenções ligadas a compras, fornecedores, cotações,
    pedidos de compra e reposição. A implementação inicial mantém o domínio
    separado das demais áreas para preservar a arquitetura modular do Cooper.
    """

    PALAVRAS_CHAVE = {
        "compra",
        "compras",
        "comprar",
        "fornecedor",
        "fornecedores",
        "cotação",
        "cotacao",
        "cotar",
        "reposição",
        "reposicao",
        "pedido de compra",
        "suprimento",
        "suprimentos",
    }

    def __init__(self) -> None:
        """Inicializa o agente de compras com seu nome padrão."""
        super().__init__(nome="compras")

    def pode_processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None
    ) -> bool:

        if analise and analise.get("dominio") == "compras":
            return True

        texto = (msg or "").lower()
        return any(palavra in texto for palavra in self.PALAVRAS_CHAVE)

    def processar(self, msg: str, analise: dict[str, Any] | None = None) -> dict[str, Any]:

        intencao = (analise or {}).get("intencao", "compras_geral")

        return self.resposta_padrao(
            status="sucesso",
            tipo=intencao,
            dados={
                "mensagem_original": msg,
                "analise": analise or {},
            },
        )
