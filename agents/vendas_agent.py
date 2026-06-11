"""
Agente de vendas do Cooper.

O agente identifica pedidos, clientes, orcamentos, faturamento e registros de
venda. Ele retorna dados estruturados para que outras camadas possam apresentar
ou executar a acao no futuro.
"""

from typing import Any

from agents.base_agent import BaseAgent
from repositories.estoque_repository import EstoqueRepository
from repositories.vendas_repository import VendasRepository


class VendasAgent(BaseAgent):
    """Agente especializado em solicitacoes de vendas."""

    PALAVRAS_CHAVE = {
        "venda",
        "vendas",
        "vender",
        "vendido",
        "pedido",
        "pedidos",
        "cliente",
        "clientes",
        "orcamento",
        "faturamento",
        "nota",
        "receita",
    }

    def __init__(
        self,
        estoque_repository: EstoqueRepository | None = None,
        vendas_repository: VendasRepository | None = None,
    ) -> None:
        super().__init__(nome="vendas")
        self.estoque_repository = estoque_repository or EstoqueRepository()
        self.vendas_repository = vendas_repository or VendasRepository()

    def pode_processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> bool:
        if analise and analise.get("dominio") == "vendas":
            return True

        texto = (msg or "").lower()
        return any(palavra in texto for palavra in self.PALAVRAS_CHAVE)

    def processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        intencao = self._definir_intencao(msg, analise=analise)
        entidades = self.entidades(analise)
        valor_texto = self.primeiro_valor_monetario(analise)
        quantidade_texto = entidades.get("quantidade") or self.primeiro_numero(analise)
        valor = self._converter_valor(valor_texto)
        quantidade = self._converter_numero(quantidade_texto)
        produto = entidades.get("produto")
        atributos = entidades.get("atributos_roupa") or {}

        dados = {
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
                valor=valor,
            ),
            "proximas_acoes": self._proximas_acoes(intencao),
        }

        dados.update(
            self._executar_acao(
                intencao=intencao,
                produto=produto,
                quantidade=quantidade,
                valor=valor,
                atributos=atributos,
            )
        )

        return self.resposta_padrao(status="sucesso", tipo=intencao, dados=dados)

    def _definir_intencao(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> str:
        if analise and analise.get("intencao"):
            return str(analise["intencao"])

        texto = (msg or "").lower()

        if "orcamento" in texto:
            return "vendas_orcamento"
        if "pedido" in texto:
            return "vendas_pedido"
        if "cliente" in texto:
            return "vendas_cliente"
        if "faturamento" in texto or "receita" in texto:
            return "vendas_faturamento"
        if "vender" in texto or "vendi" in texto or "venda" in texto:
            return "vendas_registrar"

        return "vendas_geral"

    def _resumo(self, intencao: str) -> str:
        resumos = {
            "vendas_registrar": "Registro de venda identificado.",
            "vendas_orcamento": "Solicitacao de orcamento identificada.",
            "vendas_pedido": "Consulta ou criacao de pedido identificada.",
            "vendas_cliente": "Solicitacao relacionada a cliente identificada.",
            "vendas_faturamento": "Consulta de faturamento identificada.",
        }
        return resumos.get(intencao, "Solicitacao geral de vendas identificada.")

    def _acao(self, intencao: str) -> str:
        acoes = {
            "vendas_registrar": "registrar_venda",
            "vendas_orcamento": "montar_orcamento",
            "vendas_pedido": "gerenciar_pedido",
            "vendas_cliente": "consultar_cliente",
            "vendas_faturamento": "consultar_faturamento",
        }
        return acoes.get(intencao, "analisar_vendas")

    def _campos_necessarios(
        self,
        intencao: str,
        produto: str | None,
        quantidade: float | None,
        valor: float | None,
    ) -> list[str]:
        if intencao in {"vendas_registrar", "vendas_orcamento"}:
            campos = []
            if intencao == "vendas_orcamento":
                campos.append("cliente")
            if produto is None:
                campos.append("produto")
            if quantidade is None:
                campos.append("quantidade")
            if valor is None and intencao == "vendas_registrar":
                campos.append("valor")
            return campos

        if intencao == "vendas_pedido":
            return ["numero_do_pedido_ou_cliente"]

        if intencao == "vendas_cliente":
            return ["nome_ou_documento_do_cliente"]

        if intencao == "vendas_faturamento":
            return ["periodo"]

        return ["cliente_ou_produto"]

    def _proximas_acoes(self, intencao: str) -> list[str]:
        proximas = {
            "vendas_registrar": [
                "validar cliente",
                "validar produto e quantidade",
                "registrar venda",
            ],
            "vendas_orcamento": [
                "validar cliente",
                "calcular itens",
                "gerar orcamento",
            ],
            "vendas_pedido": [
                "identificar pedido",
                "consultar status",
                "retornar detalhes",
            ],
            "vendas_cliente": [
                "identificar cliente",
                "buscar cadastro",
                "retornar historico relevante",
            ],
            "vendas_faturamento": [
                "definir periodo",
                "somar vendas",
                "retornar indicadores",
            ],
        }
        return proximas.get(intencao, ["entender solicitacao", "selecionar rotina"])

    def _executar_acao(
        self,
        intencao: str,
        produto: str | None,
        quantidade: float | None,
        valor: float | None,
        atributos: dict[str, Any],
    ) -> dict[str, Any]:
        if intencao != "vendas_registrar":
            return {"resultado": None}

        if produto is None or quantidade is None:
            return {"resultado": None}

        baixa = self.estoque_repository.registrar_saida(
            produto=produto,
            quantidade=quantidade,
            atributos=atributos,
        )

        if not baixa.get("movimento_realizado"):
            return {
                "resultado": {
                    "venda_realizada": False,
                    "produto": produto,
                    "quantidade_vendida": quantidade,
                    "motivo": baixa.get("motivo"),
                    "estoque": baixa,
                }
            }

        venda = self.vendas_repository.registrar_venda(
            produto=produto,
            quantidade=quantidade,
            valor=valor,
            produto_id=baixa.get("produto_id"),
        )

        return {
            "resultado": {
                **venda,
                "venda_realizada": True,
                "estoque": baixa,
            }
        }

    def _converter_numero(self, valor: str | None) -> float | None:
        if valor is None:
            return None

        try:
            return float(valor.replace(",", "."))
        except ValueError:
            return None

    def _converter_valor(self, valor: str | None) -> float | None:
        if valor is None:
            return None

        texto = valor.upper().replace("R$", "").strip()
        return self._converter_numero(texto)
