"""
Agente de estoque do Cooper.

Este módulo define o EstoqueAgent, responsável por reconhecer e processar
mensagens relacionadas a produtos, saldo, movimentação, entrada, saída e
inventário. O agente segue o contrato definido por BaseAgent e retorna apenas
dados estruturados.

Regra arquitetural principal:
    EstoqueAgent = lógica de domínio de estoque em formato DATA ONLY
"""

from typing import Any

from agents.base_agent import BaseAgent


class EstoqueAgent(BaseAgent):
    """
    Agente especializado em solicitações de estoque.

    Este agente identifica intenções ligadas a consulta de saldo, movimentação,
    entrada, saída, produtos e inventário. A implementação inicial separa o
    domínio de estoque das demais áreas para manter o Cooper modular.
    """

    PALAVRAS_CHAVE = {
        "estoque",
        "produto",
        "produtos",
        "saldo",
        "inventário",
        "inventario",
        "entrada",
        "saída",
        "saida",
        "movimentação",
        "movimentacao",
        "almoxarifado",
        "quantidade",
        "unidade",
    }

    def __init__(self) -> None:
        """Inicializa o agente de estoque com seu nome padrão."""
        super().__init__(nome="estoque")

    def pode_processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None
    ) -> bool:

        if analise and analise.get("dominio") == "estoque":
            return True

        texto = (msg or "").lower()
        return any(palavra in texto for palavra in self.PALAVRAS_CHAVE)

    def processar(self, msg: str, analise: dict[str, Any] | None = None) -> dict[str, Any]:

        intencao = (analise or {}).get("intencao", "estoque_geral")

        return self.resposta_padrao(
            status="sucesso",
            tipo=intencao,
            dados={
                "mensagem_original": msg,
                "analise": analise or {},
            },
        )
