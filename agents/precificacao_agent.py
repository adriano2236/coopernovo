"""Agente de precificacao do Cooper."""

from math import ceil
from typing import Any

from agents.base_agent import BaseAgent


class PrecificacaoAgent(BaseAgent):
    """Calcula sugestoes de preco de venda a partir do custo."""

    PALAVRAS_CHAVE = {
        "cobrar",
        "custo",
        "margem",
        "preco",
        "precificar",
        "reembolso",
        "sugerir",
        "sugestao",
        "valor",
    }

    def __init__(self) -> None:
        super().__init__(nome="precificacao")

    def pode_processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> bool:
        if analise:
            return analise.get("dominio") == "precificacao"

        texto = (msg or "").lower()
        return any(palavra in texto for palavra in self.PALAVRAS_CHAVE)

    def processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        entidades = self.entidades(analise)
        produto = entidades.get("produto")
        custo = self._converter_valor(self.primeiro_valor_monetario(analise))
        quantidade = self._converter_numero(entidades.get("quantidade")) or 1

        dados = {
            "mensagem_original": msg,
            "resumo": "Sugestao de preco de venda calculada.",
            "acao": "sugerir_preco_venda",
            "produto": produto,
            "atributos": entidades.get("atributos_roupa") or {},
            "entidades": entidades,
            "campos_necessarios": self._campos_necessarios(produto, custo),
            "proximas_acoes": [
                "validar custo real",
                "definir preco final com o cliente",
                "registrar pedido confirmado",
            ],
            "resultado": self._sugerir_preco(produto, custo, quantidade),
        }

        return self.resposta_padrao(
            status="sucesso",
            tipo="precificacao_sugerir_preco",
            dados=dados,
        )

    def _campos_necessarios(
        self,
        produto: str | None,
        custo: float | None,
    ) -> list[str]:
        campos = []
        if produto is None:
            campos.append("produto")
        if custo is None:
            campos.append("custo")
        return campos

    def _sugerir_preco(
        self,
        produto: str | None,
        custo: float | None,
        quantidade: float,
    ) -> dict[str, Any] | None:
        if produto is None or custo is None:
            return None

        custo_total = custo * quantidade
        multiplicador = self._multiplicador_padrao()
        preco_bruto = custo_total * multiplicador
        preco_sugerido = self._arredondar_preco(preco_bruto)

        return {
            "tipo_resultado": "precificacao",
            "produto": produto,
            "quantidade": quantidade,
            "custo_unitario": custo,
            "custo_total": custo_total,
            "multiplicador": multiplicador,
            "margem_percentual": multiplicador - 1,
            "taxa_operacional": 0,
            "lucro_sugerido": preco_sugerido - custo_total,
            "preco_sugerido": preco_sugerido,
        }

    def _multiplicador_padrao(self) -> float:
        return 2.0

    def _arredondar_preco(self, valor: float) -> float:
        return float(ceil(valor / 5) * 5)

    def _converter_numero(self, valor: str | None) -> float | None:
        if valor is None:
            return None

        try:
            return float(str(valor).replace(",", "."))
        except ValueError:
            return None

    def _converter_valor(self, valor: str | None) -> float | None:
        if valor is None:
            return None

        texto = str(valor).upper().replace("R$", "").strip()
        return self._converter_numero(texto)
