"""Agente de pedidos sob encomenda do Cooper."""

from typing import Any

from agents.base_agent import BaseAgent
from agents.precificacao_agent import PrecificacaoAgent
from repositories.pedidos_repository import PedidosRepository


class PedidosAgent(BaseAgent):
    """Agente para pedidos pre-confirmados e compras sob demanda."""

    PALAVRAS_CHAVE = {
        "cliente",
        "pedido",
        "pedidos",
        "pediu",
        "confirmei",
        "confirmar",
        "comprei",
        "entreguei",
    }

    def __init__(self, repository: PedidosRepository | None = None) -> None:
        super().__init__(nome="pedidos")
        self.repository = repository or PedidosRepository()
        self.precificacao_agent = PrecificacaoAgent()

    def pode_processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> bool:
        if analise:
            return analise.get("dominio") == "pedidos"

        texto = (msg or "").lower()
        return any(palavra in texto for palavra in self.PALAVRAS_CHAVE)

    def processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        intencao = str((analise or {}).get("intencao") or "pedidos_geral")
        entidades = self.entidades(analise)
        cliente = entidades.get("cliente")
        produto = entidades.get("produto")
        atributos = entidades.get("atributos_roupa") or {}
        quantidade = self._converter_numero(entidades.get("quantidade")) or 1
        valor = self._converter_valor(self.primeiro_valor_monetario(analise))

        dados = {
            "mensagem_original": msg,
            "resumo": self._resumo(intencao),
            "acao": self._acao(intencao),
            "cliente": cliente,
            "produto": produto,
            "atributos": atributos,
            "entidades": entidades,
            "campos_necessarios": self._campos_necessarios(
                intencao=intencao,
                cliente=cliente,
                produto=produto,
                valor=valor,
            ),
            "proximas_acoes": self._proximas_acoes(intencao),
            "resultado": self._executar_acao(
                intencao=intencao,
                cliente=cliente,
                produto=produto,
                quantidade=quantidade,
                valor=valor,
                atributos=atributos,
            ),
        }

        return self.resposta_padrao(status="sucesso", tipo=intencao, dados=dados)

    def _resumo(self, intencao: str) -> str:
        resumos = {
            "pedidos_criar": "Pedido sob encomenda registrado.",
            "pedidos_confirmar": "Confirmacao de pedido registrada.",
            "pedidos_registrar_compra": "Compra do pedido registrada.",
            "pedidos_entregar": "Entrega do pedido registrada.",
            "pedidos_concluir": "Pedido vendido, pago e concluido.",
        }
        return resumos.get(intencao, "Solicitacao de pedido identificada.")

    def _acao(self, intencao: str) -> str:
        acoes = {
            "pedidos_criar": "criar_pedido",
            "pedidos_confirmar": "confirmar_pedido",
            "pedidos_registrar_compra": "registrar_compra_pedido",
            "pedidos_entregar": "entregar_pedido",
            "pedidos_concluir": "concluir_pedido",
        }
        return acoes.get(intencao, "analisar_pedido")

    def _campos_necessarios(
        self,
        intencao: str,
        cliente: str | None,
        produto: str | None,
        valor: float | None,
    ) -> list[str]:
        campos = []
        if cliente is None and intencao not in {
            "pedidos_registrar_compra",
            "pedidos_concluir",
        }:
            campos.append("cliente")

        if intencao in {
            "pedidos_criar",
            "pedidos_registrar_compra",
            "pedidos_concluir",
        } and produto is None:
            campos.append("produto")

        if intencao == "pedidos_criar" and valor is None:
            campos.append("preco_de_venda")

        if intencao == "pedidos_registrar_compra" and valor is None:
            campos.append("custo_de_compra")

        return campos

    def _proximas_acoes(self, intencao: str) -> list[str]:
        proximas = {
            "pedidos_criar": ["confirmar interesse", "comprar peca", "entregar"],
            "pedidos_confirmar": ["comprar peca", "registrar custo"],
            "pedidos_registrar_compra": ["aguardar entrega ao cliente"],
            "pedidos_entregar": ["calcular lucro", "encerrar pedido"],
            "pedidos_concluir": ["atualizar financeiro", "acompanhar lucro"],
        }
        return proximas.get(intencao, ["entender pedido"])

    def _executar_acao(
        self,
        intencao: str,
        cliente: str | None,
        produto: str | None,
        quantidade: float,
        valor: float | None,
        atributos: dict[str, Any],
    ) -> dict[str, Any] | None:
        if intencao == "pedidos_criar" and cliente and produto:
            pedido = self.repository.criar_pedido(
                cliente=cliente,
                produto=produto,
                quantidade=quantidade,
                preco_venda=valor,
                atributos=atributos,
            )
            return self._enriquecer_pedido(pedido)

        if intencao == "pedidos_confirmar" and cliente:
            pedido = self.repository.confirmar_pedido(cliente=cliente, produto=produto)
            return self._enriquecer_pedido(pedido)

        if intencao == "pedidos_registrar_compra" and (cliente or produto):
            pedido = self.repository.registrar_compra(
                cliente=cliente,
                produto=produto,
                custo_compra=valor,
            )
            return self._com_sugestao_de_preco(pedido, valor)

        if intencao == "pedidos_entregar" and cliente:
            pedido = self.repository.entregar_pedido(cliente=cliente, produto=produto)
            return self._enriquecer_pedido(pedido)

        if intencao == "pedidos_concluir" and (cliente or produto):
            pedido = self.repository.buscar_pedido_aberto(
                cliente=cliente,
                produto=produto,
            )
            if pedido is None:
                return self.repository._nao_encontrado(cliente, produto)

            valor_final = self._valor_final_para_conclusao(pedido, valor)
            if valor_final is None:
                pedido["tipo_resultado"] = "pedido_precisa_valor"
                return pedido

            return self._registrar_pagamento_pedido(pedido, valor_final)

        return None

    def _com_sugestao_de_preco(
        self,
        pedido: dict[str, Any],
        custo_compra: float | None,
    ) -> dict[str, Any]:
        if pedido.get("tipo_resultado") == "pedido_nao_encontrado":
            return pedido

        if pedido.get("preco_venda") is not None:
            return self._enriquecer_pedido(pedido)

        if custo_compra is None:
            return self._enriquecer_pedido(pedido)

        produto = str(pedido.get("produto") or "")
        quantidade = float(pedido.get("quantidade") or 1)
        sugestao = self.precificacao_agent._sugerir_preco(
            produto=produto,
            custo=custo_compra,
            quantidade=quantidade,
        )
        if sugestao:
            pedido["sugestao_preco"] = sugestao

        return self._enriquecer_pedido(pedido)

    def _valor_final_para_conclusao(
        self,
        pedido: dict[str, Any],
        valor_informado: float | None,
    ) -> float | None:
        if valor_informado is not None:
            return valor_informado

        preco_venda = pedido.get("preco_venda")
        if preco_venda is not None:
            valor_pago = float(pedido.get("valor_pago") or 0)
            return max(float(preco_venda) - valor_pago, 0)

        custo_compra = pedido.get("custo_compra")
        if custo_compra is None:
            return None

        sugestao = self.precificacao_agent._sugerir_preco(
            produto=str(pedido.get("produto") or ""),
            custo=float(custo_compra),
            quantidade=float(pedido.get("quantidade") or 1),
        )
        if not sugestao:
            return None

        return float(sugestao.get("preco_sugerido") or 0)

    def _registrar_pagamento_pedido(
        self,
        pedido: dict[str, Any],
        valor_pago: float,
    ) -> dict[str, Any] | None:
        preco_venda = pedido.get("preco_venda")
        if preco_venda is None:
            preco_venda = valor_pago

        valor_pago_total = float(pedido.get("valor_pago") or 0) + float(valor_pago)
        status = "pago_parcial"
        if preco_venda is not None and valor_pago_total >= float(preco_venda):
            status = "concluido"

        atualizado = self.repository.atualizar_pagamento(
            pedido_id=int(pedido["pedido_id"]),
            preco_venda=float(preco_venda) if preco_venda is not None else None,
            valor_pago_total=valor_pago_total,
            status=status,
        )
        return self._enriquecer_pedido(atualizado)

    def _enriquecer_pedido(
        self,
        pedido: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not pedido or pedido.get("tipo_resultado") != "pedido":
            return pedido

        preco = pedido.get("preco_venda")
        custo = pedido.get("custo_compra")
        valor_pago = pedido.get("valor_pago")
        receita = valor_pago if valor_pago is not None else preco

        if preco is not None:
            pedido["valor_restante"] = max(float(preco) - float(valor_pago or 0), 0)

        if receita is not None and custo is not None:
            pedido["lucro"] = float(receita) - float(custo)

        return pedido

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
