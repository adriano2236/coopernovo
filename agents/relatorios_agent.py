"""Agente de relatorios do Cooper."""

from typing import Any

from agents.base_agent import BaseAgent
from repositories.contas_repository import ContasRepository
from repositories.estoque_repository import EstoqueRepository
from repositories.pedidos_repository import PedidosRepository
from repositories.vendas_repository import VendasRepository


class RelatoriosAgent(BaseAgent):
    """Agente especializado em relatorios simples de loja."""

    PALAVRAS_CHAVE = {
        "relatorio",
        "relatorios",
        "historico",
        "baixo",
        "baixos",
        "fechamento",
        "fechar",
        "resumo",
    }

    def __init__(
        self,
        estoque_repository: EstoqueRepository | None = None,
        vendas_repository: VendasRepository | None = None,
        pedidos_repository: PedidosRepository | None = None,
        contas_repository: ContasRepository | None = None,
    ) -> None:
        super().__init__(nome="relatorios")
        self.estoque_repository = estoque_repository or EstoqueRepository()
        self.vendas_repository = vendas_repository or VendasRepository()
        self.pedidos_repository = pedidos_repository or PedidosRepository()
        self.contas_repository = contas_repository or ContasRepository()

    def pode_processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> bool:
        if analise:
            return analise.get("dominio") == "relatorios"

        texto = (msg or "").lower()
        return any(palavra in texto for palavra in self.PALAVRAS_CHAVE)

    def processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        intencao = str((analise or {}).get("intencao") or "relatorios_geral")
        entidades = self.entidades(analise)
        produto = entidades.get("produto")
        atributos = entidades.get("atributos_roupa") or {}
        limite = self._limite_estoque_baixo(analise)

        dados = {
            "mensagem_original": msg,
            "resumo": self._resumo(intencao),
            "acao": self._acao(intencao),
            "produto": produto,
            "atributos": atributos,
            "entidades": entidades,
            "campos_necessarios": self._campos_necessarios(intencao, produto),
            "proximas_acoes": self._proximas_acoes(intencao),
            "resultado": self._executar_acao(
                intencao=intencao,
                produto=produto,
                atributos=atributos,
                limite=limite,
            ),
        }

        return self.resposta_padrao(status="sucesso", tipo=intencao, dados=dados)

    def _resumo(self, intencao: str) -> str:
        resumos = {
            "relatorios_vendas_hoje": "Resumo de vendas de hoje.",
            "relatorios_estoque_baixo": "Produtos com estoque baixo.",
            "relatorios_historico_produto": "Historico de movimentacoes do produto.",
            "relatorios_pedidos_pendentes": "Pedidos pendentes.",
            "relatorios_pedidos_concluidos": "Pedidos concluidos.",
            "relatorios_compras_pendentes": "Compras pendentes.",
            "relatorios_valor_receber": "Valor a receber dos pedidos.",
            "relatorios_lucro": "Lucro dos pedidos.",
            "relatorios_fechamento_dia": "Fechamento do dia calculado.",
        }
        return resumos.get(intencao, "Relatorio solicitado.")

    def _acao(self, intencao: str) -> str:
        acoes = {
            "relatorios_vendas_hoje": "resumir_vendas_hoje",
            "relatorios_estoque_baixo": "listar_estoque_baixo",
            "relatorios_historico_produto": "consultar_historico_produto",
            "relatorios_pedidos_pendentes": "listar_pedidos_pendentes",
            "relatorios_pedidos_concluidos": "listar_pedidos_concluidos",
            "relatorios_compras_pendentes": "listar_compras_pendentes",
            "relatorios_valor_receber": "calcular_valor_a_receber",
            "relatorios_lucro": "calcular_lucro",
            "relatorios_fechamento_dia": "calcular_fechamento_dia",
        }
        return acoes.get(intencao, "analisar_relatorio")

    def _campos_necessarios(self, intencao: str, produto: str | None) -> list[str]:
        if intencao == "relatorios_historico_produto" and produto is None:
            return ["produto"]

        return []

    def _proximas_acoes(self, intencao: str) -> list[str]:
        proximas = {
            "relatorios_vendas_hoje": [
                "somar vendas do periodo",
                "agrupar produtos vendidos",
            ],
            "relatorios_estoque_baixo": [
                "consultar saldos",
                "listar produtos abaixo do limite",
            ],
            "relatorios_historico_produto": [
                "identificar produto",
                "buscar movimentos recentes",
            ],
            "relatorios_pedidos_pendentes": [
                "buscar pedidos nao entregues",
                "listar proximas acoes",
            ],
            "relatorios_pedidos_concluidos": [
                "buscar pedidos encerrados",
                "listar vendas ja recebidas",
            ],
            "relatorios_compras_pendentes": [
                "buscar pedidos sem compra registrada",
                "listar compras necessarias",
            ],
            "relatorios_valor_receber": [
                "somar pedidos ainda nao entregues",
                "retornar valor a receber",
            ],
            "relatorios_lucro": [
                "somar pedidos com custo conhecido",
                "retornar lucro conhecido",
            ],
            "relatorios_fechamento_dia": [
                "somar movimentacoes do dia",
                "mostrar pendencias atuais",
            ],
        }
        return proximas.get(intencao, ["identificar relatorio"])

    def _executar_acao(
        self,
        intencao: str,
        produto: str | None,
        atributos: dict[str, Any],
        limite: float,
    ) -> dict[str, Any] | None:
        if intencao == "relatorios_fechamento_dia":
            return self._fechamento_dia()

        if intencao == "relatorios_vendas_hoje":
            return self.vendas_repository.resumo_hoje()

        if intencao == "relatorios_estoque_baixo":
            return {
                "tipo_relatorio": "estoque_baixo",
                "limite": limite,
                "itens": self.estoque_repository.listar_estoque_baixo(limite),
            }

        if intencao == "relatorios_historico_produto" and produto:
            historico = self.estoque_repository.historico(produto, atributos)
            return {
                "tipo_relatorio": "historico_produto",
                "produto_consultado": produto,
                "historico": historico,
            }

        if intencao == "relatorios_pedidos_pendentes":
            return {
                "tipo_relatorio": "pedidos_pendentes",
                "itens": self._enriquecer_pedidos(
                    self.pedidos_repository.listar_pedidos_pendentes()
                ),
            }

        if intencao == "relatorios_pedidos_concluidos":
            return {
                "tipo_relatorio": "pedidos_concluidos",
                "itens": self._enriquecer_pedidos(
                    self.pedidos_repository.listar_pedidos_concluidos()
                ),
            }

        if intencao == "relatorios_compras_pendentes":
            return {
                "tipo_relatorio": "compras_pendentes",
                "itens": self._enriquecer_pedidos(
                    self.pedidos_repository.listar_compras_pendentes()
                ),
            }

        if intencao == "relatorios_valor_receber":
            return self.pedidos_repository.resumo_financeiro()

        if intencao == "relatorios_lucro":
            return self.pedidos_repository.resumo_financeiro()

        return None

    def _fechamento_dia(self) -> dict[str, Any]:
        compras_pendentes = self._enriquecer_pedidos(
            self.pedidos_repository.listar_compras_pendentes()
        )
        para_cobrar = self._enriquecer_pedidos(
            self.pedidos_repository.listar_pedidos_para_cobrar()
        )
        para_entregar = self._enriquecer_pedidos(
            self.pedidos_repository.listar_pedidos_para_entregar()
        )

        return {
            "tipo_relatorio": "fechamento_dia",
            "periodo": "hoje",
            "pedidos": self.pedidos_repository.resumo_hoje(),
            "caixa": self.contas_repository.resumo_caixa_hoje(),
            "despesas": self.contas_repository.resumo_despesas_hoje(),
            "vendas": self.vendas_repository.resumo_hoje(),
            "financeiro": self.pedidos_repository.resumo_financeiro(),
            "pendencias": {
                "compras_pendentes": len(compras_pendentes),
                "para_cobrar": len(para_cobrar),
                "para_entregar": len(para_entregar),
            },
        }

    def _limite_estoque_baixo(self, analise: dict[str, Any] | None) -> float:
        numero = self.primeiro_numero(analise)
        if numero is None:
            return 3

        try:
            return float(numero.replace(",", "."))
        except ValueError:
            return 3

    def _enriquecer_pedidos(
        self,
        pedidos: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return [self._enriquecer_pedido(pedido) for pedido in pedidos]

    def _enriquecer_pedido(self, pedido: dict[str, Any]) -> dict[str, Any]:
        preco = pedido.get("preco_venda")
        custo = pedido.get("custo_compra")
        valor_pago = pedido.get("valor_pago")
        receita = valor_pago if valor_pago is not None else preco

        if preco is not None:
            pedido["valor_restante"] = max(float(preco) - float(valor_pago or 0), 0)

        if receita is not None and custo is not None:
            pedido["lucro"] = float(receita) - float(custo)

        return pedido
