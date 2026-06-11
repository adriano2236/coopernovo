"""
Agente de estoque do Cooper.

O agente identifica solicitacoes de produtos, saldo, entradas, saidas e
inventario. Ele ainda nao persiste dados; por enquanto transforma a mensagem em
um plano estruturado para a camada de resposta ou para futuras acoes reais.
"""

from typing import Any

from agents.base_agent import BaseAgent
from repositories.estoque_repository import EstoqueRepository


class EstoqueAgent(BaseAgent):
    """Agente especializado em solicitacoes de estoque."""

    PALAVRAS_CHAVE = {
        "estoque",
        "produto",
        "produtos",
        "saldo",
        "inventario",
        "entrada",
        "saida",
        "movimentacao",
        "almoxarifado",
        "quantidade",
        "unidade",
    }

    def __init__(self, repository: EstoqueRepository | None = None) -> None:
        super().__init__(nome="estoque")
        self.repository = repository or EstoqueRepository()

    def pode_processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> bool:
        if analise and analise.get("dominio") == "estoque":
            return True

        texto = (msg or "").lower()
        return any(palavra in texto for palavra in self.PALAVRAS_CHAVE)

    def processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        intencao = str((analise or {}).get("intencao") or "estoque_geral")
        entidades = self.entidades(analise)
        quantidade_texto = self.primeiro_numero(analise)
        quantidade = self._converter_quantidade(quantidade_texto)
        produto = entidades.get("produto")
        atributos = entidades.get("atributos_roupa") or {}

        dados_base = {
            "mensagem_original": msg,
            "resumo": self._resumo(intencao),
            "acao": self._acao(intencao),
            "produto": produto,
            "atributos": atributos,
            "entidades": entidades,
            "campos_necessarios": self._campos_necessarios(
                intencao,
                produto=produto,
                quantidade=quantidade,
            ),
            "proximas_acoes": self._proximas_acoes(intencao),
        }

        dados_base.update(
            self._executar_acao(
                intencao,
                produto,
                quantidade,
                atributos,
            )
        )

        return self.resposta_padrao(
            status="sucesso",
            tipo=intencao,
            dados=dados_base,
        )

    def _resumo(self, intencao: str) -> str:
        resumos = {
            "estoque_consulta_saldo": "Consulta de saldo de produto identificada.",
            "estoque_entrada": "Registro de entrada de estoque identificado.",
            "estoque_saida": "Registro de saida de estoque identificado.",
            "estoque_inventario": "Solicitacao de inventario identificada.",
        }
        return resumos.get(intencao, "Solicitacao geral de estoque identificada.")

    def _acao(self, intencao: str) -> str:
        acoes = {
            "estoque_consulta_saldo": "consultar_saldo",
            "estoque_entrada": "registrar_entrada",
            "estoque_saida": "registrar_saida",
            "estoque_inventario": "gerar_inventario",
        }
        return acoes.get(intencao, "analisar_estoque")

    def _campos_necessarios(
        self,
        intencao: str,
        produto: str | None,
        quantidade: float | None,
    ) -> list[str]:
        if intencao == "estoque_consulta_saldo":
            return [] if produto else ["produto"]

        if intencao in {"estoque_entrada", "estoque_saida"}:
            campos = []
            if produto is None:
                campos.append("produto")
            if quantidade is None:
                campos.append("quantidade")
            return campos

        if intencao == "estoque_inventario":
            return []

        return ["produto_ou_criterio"]

    def _proximas_acoes(self, intencao: str) -> list[str]:
        proximas = {
            "estoque_consulta_saldo": [
                "identificar o produto",
                "buscar saldo atual",
                "retornar quantidade disponivel",
            ],
            "estoque_entrada": [
                "validar produto e quantidade",
                "registrar entrada",
                "atualizar saldo",
            ],
            "estoque_saida": [
                "validar produto e quantidade",
                "conferir saldo disponivel",
                "registrar saida",
            ],
            "estoque_inventario": [
                "definir criterio do inventario",
                "listar produtos",
                "apontar divergencias",
            ],
        }
        return proximas.get(
            intencao,
            ["entender criterio", "selecionar rotina de estoque"],
        )

    def _executar_acao(
        self,
        intencao: str,
        produto: str | None,
        quantidade: float | None,
        atributos: dict[str, Any],
    ) -> dict[str, Any]:
        if intencao == "estoque_consulta_saldo" and produto:
            item = self.repository.consultar(produto, atributos)
            return {
                "resultado": item or {
                    "produto": produto,
                    "quantidade": 0,
                    "cadastrado": False,
                }
            }

        if intencao == "estoque_entrada" and produto and quantidade is not None:
            return {
                "resultado": self.repository.registrar_entrada(
                    produto,
                    quantidade,
                    atributos,
                )
            }

        if intencao == "estoque_saida" and produto and quantidade is not None:
            resultado = self.repository.registrar_saida(
                produto,
                quantidade,
                atributos,
            )
            return {"resultado": resultado}

        if intencao == "estoque_inventario":
            return {"resultado": {"itens": self.repository.listar()}}

        return {"resultado": None}

    def _converter_quantidade(self, valor: str | None) -> float | None:
        if valor is None:
            return None

        try:
            return float(valor.replace(",", "."))
        except ValueError:
            return None
