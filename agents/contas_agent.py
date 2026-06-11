"""Agente contador do Cooper."""

from typing import Any

from agents.base_agent import BaseAgent
from repositories.contas_repository import ContasRepository
from repositories.pedidos_repository import PedidosRepository


class ContasAgent(BaseAgent):
    """Agente especializado na visao financeira do negocio."""

    PALAVRAS_CHAVE = {
        "caixa",
        "contador",
        "contas",
        "deve",
        "devendo",
        "financeiro",
        "lucro",
        "pagou",
        "receber",
        "recebi",
    }

    def __init__(
        self,
        pedidos_repository: PedidosRepository | None = None,
        contas_repository: ContasRepository | None = None,
    ) -> None:
        super().__init__(nome="contas")
        self.pedidos_repository = pedidos_repository or PedidosRepository()
        self.contas_repository = contas_repository or ContasRepository()

    def pode_processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> bool:
        if analise:
            return analise.get("dominio") == "contas"

        texto = (msg or "").lower()
        return any(palavra in texto for palavra in self.PALAVRAS_CHAVE)

    def processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        intencao = str((analise or {}).get("intencao") or "contas_resumo")
        entidades = self.entidades(analise)
        cliente = entidades.get("cliente")
        produto = entidades.get("produto")
        valor = self._converter_valor(self.primeiro_valor_monetario(analise))
        resultado = self._executar_acao(
            intencao=intencao,
            cliente=cliente,
            produto=produto,
            valor=valor,
        )

        dados = {
            "mensagem_original": msg,
            "resumo": self._resumo(intencao),
            "acao": self._acao(intencao),
            "cliente": cliente,
            "produto": produto,
            "entidades": entidades,
            "campos_necessarios": self._campos_necessarios(
                intencao=intencao,
                cliente=cliente,
                valor=valor,
            ),
            "proximas_acoes": self._proximas_acoes(intencao),
            "resultado": resultado,
        }

        return self.resposta_padrao(status="sucesso", tipo=intencao, dados=dados)

    def _resumo(self, intencao: str) -> str:
        resumos = {
            "contas_a_receber": "Valor a receber calculado.",
            "contas_lucro": "Lucro dos pedidos calculado.",
            "contas_consultar_cliente": "Divida do cliente consultada.",
            "contas_registrar_divida": "Conta a receber registrada.",
            "contas_registrar_pagamento": "Pagamento registrado.",
            "contas_resumo": "Resumo financeiro calculado.",
        }
        return resumos.get(intencao, "Resumo financeiro calculado.")

    def _acao(self, intencao: str) -> str:
        acoes = {
            "contas_a_receber": "calcular_a_receber",
            "contas_lucro": "calcular_lucro",
            "contas_consultar_cliente": "consultar_cliente",
            "contas_registrar_divida": "registrar_divida",
            "contas_registrar_pagamento": "registrar_pagamento",
            "contas_resumo": "resumir_contas",
        }
        return acoes.get(intencao, "resumir_contas")

    def _campos_necessarios(
        self,
        intencao: str,
        cliente: str | None,
        valor: float | None,
    ) -> list[str]:
        campos = []
        if intencao in {
            "contas_consultar_cliente",
            "contas_registrar_divida",
            "contas_registrar_pagamento",
        } and cliente is None:
            campos.append("cliente")

        if intencao in {"contas_registrar_divida", "contas_registrar_pagamento"} and valor is None:
            campos.append("valor")

        return campos

    def _proximas_acoes(self, intencao: str) -> list[str]:
        proximas = {
            "contas_a_receber": ["acompanhar pedidos em aberto"],
            "contas_lucro": ["comparar venda recebida e custo de compra"],
            "contas_consultar_cliente": ["acompanhar saldo do cliente"],
            "contas_registrar_divida": ["registrar pagamentos quando receber"],
            "contas_registrar_pagamento": ["acompanhar saldo restante"],
            "contas_resumo": ["acompanhar caixa", "acompanhar lucro"],
        }
        return proximas.get(intencao, ["acompanhar financeiro"])

    def _executar_acao(
        self,
        intencao: str,
        cliente: str | None,
        produto: str | None,
        valor: float | None,
    ) -> dict[str, Any] | None:
        if intencao == "contas_registrar_divida" and cliente and valor is not None:
            conta = self.contas_repository.registrar_divida(
                cliente=cliente,
                valor_total=valor,
                descricao=None,
            )
            return self._enriquecer_conta(conta)

        if intencao == "contas_registrar_pagamento" and cliente and valor is not None:
            return self._registrar_pagamento(
                cliente=cliente,
                produto=produto,
                valor=valor,
            )

        if intencao == "contas_consultar_cliente" and cliente:
            return self._resumo_cliente(cliente)

        resumo = self._resumo_geral()
        resumo["visao"] = self._visao(intencao)
        return resumo

    def _registrar_pagamento(
        self,
        cliente: str,
        produto: str | None,
        valor: float,
    ) -> dict[str, Any]:
        pedido = self.pedidos_repository.buscar_pedido_aberto(
            cliente=cliente,
            produto=produto,
        )
        if pedido and pedido.get("preco_venda") is not None:
            return self._registrar_pagamento_pedido(pedido, valor)

        conta = self.contas_repository.buscar_conta_aberta(cliente)
        if conta:
            return self._registrar_pagamento_conta(conta, valor)

        return {
            "tipo_resultado": "conta_nao_encontrada",
            "cliente": cliente,
        }

    def _registrar_pagamento_pedido(
        self,
        pedido: dict[str, Any],
        valor: float,
    ) -> dict[str, Any]:
        preco_venda = float(pedido.get("preco_venda") or 0)
        valor_pago_total = float(pedido.get("valor_pago") or 0) + float(valor)
        status = "concluido" if valor_pago_total >= preco_venda else "pago_parcial"
        atualizado = self.pedidos_repository.atualizar_pagamento(
            pedido_id=int(pedido["pedido_id"]),
            preco_venda=preco_venda,
            valor_pago_total=valor_pago_total,
            status=status,
        )
        return self._enriquecer_pedido(atualizado or pedido)

    def _registrar_pagamento_conta(
        self,
        conta: dict[str, Any],
        valor: float,
    ) -> dict[str, Any]:
        valor_total = float(conta.get("valor_total") or 0)
        valor_pago_total = float(conta.get("valor_pago") or 0) + float(valor)
        valor_restante = max(valor_total - valor_pago_total, 0)
        status = "quitado" if valor_restante == 0 else "pago_parcial"
        atualizado = self.contas_repository.atualizar_pagamento(
            conta_id=int(conta["conta_id"]),
            valor_pago_total=valor_pago_total,
            status=status,
        )
        return self._enriquecer_conta(atualizado or conta)

    def _enriquecer_conta(
        self,
        conta: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not conta or conta.get("tipo_resultado") != "conta_receber":
            return conta

        valor_total = float(conta.get("valor_total") or 0)
        valor_pago = float(conta.get("valor_pago") or 0)
        conta["valor_restante"] = max(valor_total - valor_pago, 0)
        return conta

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

    def _resumo_cliente(self, cliente: str) -> dict[str, Any]:
        pedidos = self.pedidos_repository.resumo_cliente(cliente)
        contas = self.contas_repository.resumo_cliente(cliente)
        return {
            "tipo_resultado": "conta_resumo_cliente",
            "cliente": cliente,
            "total_pedidos": pedidos.get("total_pedidos", 0),
            "total_contas": contas.get("total_contas", 0),
            "valor_total": float(pedidos.get("valor_total") or 0)
            + float(contas.get("valor_total") or 0),
            "valor_pago": float(pedidos.get("valor_pago") or 0)
            + float(contas.get("valor_pago") or 0),
            "valor_restante": float(pedidos.get("valor_restante") or 0)
            + float(contas.get("valor_restante") or 0),
        }

    def _resumo_geral(self) -> dict[str, Any]:
        pedidos = self.pedidos_repository.resumo_financeiro()
        contas = self.contas_repository.resumo()
        return {
            "tipo_relatorio": "contas_resumo",
            "total_pedidos": pedidos.get("total_pedidos", 0),
            "total_contas": contas.get("total_contas", 0),
            "valor_a_receber": float(pedidos.get("valor_a_receber") or 0)
            + float(contas.get("valor_a_receber") or 0),
            "valor_recebido": float(pedidos.get("valor_recebido") or 0)
            + float(contas.get("valor_recebido") or 0),
            "custos_realizados": pedidos.get("custos_realizados", 0),
            "lucro_conhecido": pedidos.get("lucro_conhecido", 0),
            "lucro_realizado": pedidos.get("lucro_realizado", 0),
        }

    def _visao(self, intencao: str) -> str:
        if intencao == "contas_a_receber":
            return "a_receber"
        if intencao == "contas_lucro":
            return "lucro"
        return "resumo"

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
