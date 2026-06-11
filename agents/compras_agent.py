"""
Agente de compras do Cooper.

O agente identifica compras, fornecedores, cotacoes e reposicao. Ele ainda nao
executa compras reais; devolve um plano estruturado para orientar os proximos
passos do sistema.
"""

from typing import Any

from agents.base_agent import BaseAgent


class ComprasAgent(BaseAgent):
    """Agente especializado em solicitacoes de compras."""

    PALAVRAS_CHAVE = {
        "compra",
        "compras",
        "comprar",
        "fornecedor",
        "fornecedores",
        "cotacao",
        "cotar",
        "reposicao",
        "pedido de compra",
        "suprimento",
        "suprimentos",
    }

    def __init__(self) -> None:
        super().__init__(nome="compras")

    def pode_processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> bool:
        if analise and analise.get("dominio") == "compras":
            return True

        texto = (msg or "").lower()
        return any(palavra in texto for palavra in self.PALAVRAS_CHAVE)

    def processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        intencao = str((analise or {}).get("intencao") or "compras_geral")
        quantidade = self.primeiro_numero(analise)

        return self.resposta_padrao(
            status="sucesso",
            tipo=intencao,
            dados={
                "mensagem_original": msg,
                "resumo": self._resumo(intencao),
                "acao": self._acao(intencao),
                "entidades": self.entidades(analise),
                "campos_necessarios": self._campos_necessarios(
                    intencao,
                    quantidade=quantidade,
                ),
                "proximas_acoes": self._proximas_acoes(intencao),
            },
        )

    def _resumo(self, intencao: str) -> str:
        resumos = {
            "compras_registrar": "Registro de compra identificado.",
            "compras_cotacao": "Solicitacao de cotacao identificada.",
            "compras_fornecedor": "Solicitacao relacionada a fornecedor identificada.",
            "compras_reposicao": "Necessidade de reposicao identificada.",
        }
        return resumos.get(intencao, "Solicitacao geral de compras identificada.")

    def _acao(self, intencao: str) -> str:
        acoes = {
            "compras_registrar": "registrar_compra",
            "compras_cotacao": "solicitar_cotacao",
            "compras_fornecedor": "consultar_fornecedor",
            "compras_reposicao": "planejar_reposicao",
        }
        return acoes.get(intencao, "analisar_compras")

    def _campos_necessarios(
        self,
        intencao: str,
        quantidade: str | None,
    ) -> list[str]:
        if intencao in {"compras_registrar", "compras_cotacao", "compras_reposicao"}:
            campos = ["produto"]
            if quantidade is None:
                campos.append("quantidade")
            if intencao == "compras_cotacao":
                campos.append("fornecedor_ou_lista_de_fornecedores")
            return campos

        if intencao == "compras_fornecedor":
            return ["nome_ou_documento_do_fornecedor"]

        return ["produto_ou_fornecedor"]

    def _proximas_acoes(self, intencao: str) -> list[str]:
        proximas = {
            "compras_registrar": [
                "validar fornecedor",
                "validar produto e quantidade",
                "registrar compra",
            ],
            "compras_cotacao": [
                "identificar produto",
                "selecionar fornecedores",
                "montar solicitacao de cotacao",
            ],
            "compras_fornecedor": [
                "identificar fornecedor",
                "buscar cadastro",
                "retornar condicoes comerciais",
            ],
            "compras_reposicao": [
                "avaliar estoque minimo",
                "calcular quantidade sugerida",
                "gerar pedido de compra",
            ],
        }
        return proximas.get(intencao, ["entender solicitacao", "selecionar rotina"])
