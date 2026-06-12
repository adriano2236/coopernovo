"""Agente de pedidos sob encomenda do Cooper."""

from typing import Any

from agents.base_agent import BaseAgent
from agents.precificacao_agent import PrecificacaoAgent
from repositories.pedidos_repository import PedidosRepository


class PedidosAgent(BaseAgent):
    """Agente para pedidos pre-confirmados e compras sob demanda."""

    PALAVRAS_CHAVE = {
        "altera",
        "alterar",
        "cancela",
        "cancelar",
        "cancelei",
        "cliente",
        "pedido",
        "pedidos",
        "pediu",
        "corrige",
        "editar",
        "troca",
        "muda",
        "confirmei",
        "confirmar",
        "comprei",
        "entreguei",
        "historico",
        "pagamento",
        "pagou",
        "pago",
        "recebi",
        "recebido",
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
        pedido_id = self._converter_pedido_id(entidades.get("pedido_id"))
        edicao = entidades.get("edicao_pedido") or {}
        produto = self._produto_contextual(
            intencao=intencao,
            cliente=cliente,
            produto=produto,
            entidades=entidades,
        )
        atributos = entidades.get("atributos_roupa") or {}
        quantidade = self._converter_numero(entidades.get("quantidade")) or 1
        valor = self._converter_valor(self.primeiro_valor_monetario(analise))

        dados = {
            "mensagem_original": msg,
            "resumo": self._resumo(intencao),
            "acao": self._acao(intencao),
            "pedido_id": pedido_id,
            "cliente": cliente,
            "produto": produto,
            "atributos": atributos,
            "edicao": edicao,
            "entidades": entidades,
            "campos_necessarios": self._campos_necessarios(
                intencao=intencao,
                pedido_id=pedido_id,
                cliente=cliente,
                produto=produto,
                valor=valor,
                edicao=edicao,
            ),
            "proximas_acoes": self._proximas_acoes(intencao),
            "resultado": self._executar_acao(
                intencao=intencao,
                pedido_id=pedido_id,
                cliente=cliente,
                produto=produto,
                quantidade=quantidade,
                valor=valor,
                atributos=atributos,
                edicao=edicao,
            ),
        }

        return self.resposta_padrao(status="sucesso", tipo=intencao, dados=dados)

    def _resumo(self, intencao: str) -> str:
        resumos = {
            "pedidos_criar": "Pedido sob encomenda registrado.",
            "pedidos_confirmar": "Confirmacao de pedido registrada.",
            "pedidos_registrar_compra": "Compra do pedido registrada.",
            "pedidos_registrar_pagamento": "Pagamento do pedido registrado.",
            "pedidos_entregar": "Entrega do pedido registrada.",
            "pedidos_concluir": "Pedido vendido, pago e concluido.",
            "pedidos_editar": "Pedido atualizado.",
            "pedidos_cancelar": "Pedido cancelado.",
            "pedidos_historico": "Historico do pedido recuperado.",
        }
        return resumos.get(intencao, "Solicitacao de pedido identificada.")

    def _acao(self, intencao: str) -> str:
        acoes = {
            "pedidos_criar": "criar_pedido",
            "pedidos_confirmar": "confirmar_pedido",
            "pedidos_registrar_compra": "registrar_compra_pedido",
            "pedidos_registrar_pagamento": "registrar_pagamento_pedido",
            "pedidos_entregar": "entregar_pedido",
            "pedidos_concluir": "concluir_pedido",
            "pedidos_editar": "editar_pedido",
            "pedidos_cancelar": "cancelar_pedido",
            "pedidos_historico": "consultar_historico_pedido",
        }
        return acoes.get(intencao, "analisar_pedido")

    def _campos_necessarios(
        self,
        intencao: str,
        pedido_id: int | None,
        cliente: str | None,
        produto: str | None,
        valor: float | None,
        edicao: dict[str, Any],
    ) -> list[str]:
        campos = []
        if cliente is None and pedido_id is None and intencao not in {
            "pedidos_registrar_compra",
            "pedidos_registrar_pagamento",
            "pedidos_entregar",
            "pedidos_concluir",
            "pedidos_confirmar",
            "pedidos_editar",
            "pedidos_cancelar",
            "pedidos_historico",
        }:
            campos.append("cliente")

        if intencao in {
            "pedidos_criar",
        } and produto is None:
            campos.append("produto")

        if intencao in {
            "pedidos_registrar_compra",
            "pedidos_registrar_pagamento",
            "pedidos_entregar",
            "pedidos_concluir",
            "pedidos_confirmar",
            "pedidos_editar",
            "pedidos_cancelar",
            "pedidos_historico",
        } and pedido_id is None and cliente is None and produto is None:
            campos.append("pedido_cliente_ou_produto")

        if intencao == "pedidos_criar" and valor is None:
            campos.append("preco_de_venda")

        if intencao == "pedidos_registrar_compra" and valor is None:
            campos.append("custo_de_compra")

        if intencao == "pedidos_registrar_pagamento" and valor is None:
            campos.append("valor_pago")

        if intencao == "pedidos_editar" and not edicao and valor is None:
            campos.append("campo_para_alterar")

        return campos

    def _proximas_acoes(self, intencao: str) -> list[str]:
        proximas = {
            "pedidos_criar": ["confirmar interesse", "comprar peca", "entregar"],
            "pedidos_confirmar": ["comprar peca", "registrar custo"],
            "pedidos_registrar_compra": ["definir preco", "receber pagamento"],
            "pedidos_registrar_pagamento": ["acompanhar saldo", "entregar peca"],
            "pedidos_entregar": ["conferir pagamento", "encerrar pedido"],
            "pedidos_concluir": ["atualizar financeiro", "acompanhar lucro"],
            "pedidos_editar": ["conferir pedido atualizado"],
            "pedidos_cancelar": ["acompanhar pedidos ativos"],
            "pedidos_historico": ["revisar linha do tempo do pedido"],
        }
        return proximas.get(intencao, ["entender pedido"])

    def _executar_acao(
        self,
        intencao: str,
        pedido_id: int | None,
        cliente: str | None,
        produto: str | None,
        quantidade: float,
        valor: float | None,
        atributos: dict[str, Any],
        edicao: dict[str, Any],
    ) -> dict[str, Any] | None:
        if intencao == "pedidos_historico" and (pedido_id or cliente or produto):
            pedido = self._buscar_pedido_para_historico(pedido_id, cliente, produto)
            if pedido is None:
                return self._pedido_nao_encontrado(pedido_id, cliente, produto)
            return self._historico_pedido(pedido)

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

        if (
            intencao == "pedidos_registrar_pagamento"
            and (pedido_id or cliente or produto)
            and valor is not None
        ):
            pedido = self._buscar_pedido_para_acao(pedido_id, cliente, produto)
            if pedido is None:
                return self._pedido_nao_encontrado(pedido_id, cliente, produto)
            return self._registrar_pagamento_pedido(pedido, valor)

        if intencao == "pedidos_entregar" and (pedido_id or cliente or produto):
            pedido = self._buscar_pedido_para_acao(pedido_id, cliente, produto)
            if pedido is None:
                return self._pedido_nao_encontrado(pedido_id, cliente, produto)
            return self._registrar_entrega_pedido(pedido)

        if intencao == "pedidos_concluir" and (pedido_id or cliente or produto):
            pedido = self._buscar_pedido_para_acao(pedido_id, cliente, produto)
            if pedido is None:
                return self._pedido_nao_encontrado(pedido_id, cliente, produto)

            return self._concluir_pedido(pedido, valor)

        if intencao == "pedidos_cancelar" and (pedido_id or cliente or produto):
            pedido = self._buscar_pedido_para_acao(pedido_id, cliente, produto)
            if pedido is None:
                return self._pedido_nao_encontrado(pedido_id, cliente, produto)
            cancelado = self.repository.cancelar_pedido(
                pedido_id=int(pedido["pedido_id"]),
            )
            return self._enriquecer_pedido(cancelado)

        if intencao == "pedidos_editar" and (pedido_id or cliente or produto):
            pedido = self._buscar_pedido_para_acao(pedido_id, cliente, produto)
            if pedido is None:
                return self._pedido_nao_encontrado(pedido_id, cliente, produto)
            return self._editar_pedido(
                pedido=pedido,
                edicao=edicao,
                valor_padrao=valor,
            )

        return None

    def _buscar_pedido_para_acao(
        self,
        pedido_id: int | None,
        cliente: str | None,
        produto: str | None,
    ) -> dict[str, Any] | None:
        if pedido_id is not None:
            pedido = self.repository.buscar_por_id(pedido_id)
            if not pedido:
                return None
            if pedido.get("status") in {"cancelado", "concluido"}:
                return None
            return pedido

        return self.repository.buscar_pedido_aberto(
            cliente=cliente,
            produto=produto,
        )

    def _buscar_pedido_para_historico(
        self,
        pedido_id: int | None,
        cliente: str | None,
        produto: str | None,
    ) -> dict[str, Any] | None:
        if pedido_id is not None:
            return self.repository.buscar_por_id(pedido_id)

        return self.repository.buscar_mais_recente(
            cliente=cliente,
            produto=produto,
        )

    def _historico_pedido(self, pedido: dict[str, Any]) -> dict[str, Any]:
        pedido_enriquecido = self._enriquecer_pedido(pedido) or pedido
        return {
            "tipo_resultado": "pedido_historico",
            "pedido": pedido_enriquecido,
            "itens": self.repository.listar_historico(
                int(pedido_enriquecido["pedido_id"])
            ),
        }

    def _pedido_nao_encontrado(
        self,
        pedido_id: int | None,
        cliente: str | None,
        produto: str | None,
    ) -> dict[str, Any]:
        resultado = self.repository._nao_encontrado(cliente, produto)
        if pedido_id is not None:
            resultado["pedido_id"] = pedido_id
        return resultado

    def _editar_pedido(
        self,
        pedido: dict[str, Any],
        edicao: dict[str, Any],
        valor_padrao: float | None,
    ) -> dict[str, Any] | None:
        alteracoes = self._preparar_alteracoes_pedido(
            pedido=pedido,
            edicao=edicao,
            valor_padrao=valor_padrao,
        )
        if not alteracoes:
            pedido["tipo_resultado"] = "pedido_sem_alteracao"
            return self._enriquecer_pedido(pedido)

        atualizado = self.repository.atualizar_pedido(
            pedido_id=int(pedido["pedido_id"]),
            produto=alteracoes.get("produto"),
            quantidade=alteracoes.get("quantidade"),
            preco_venda=alteracoes.get("preco_venda"),
            custo_compra=alteracoes.get("custo_compra"),
            atributos=alteracoes.get("atributos"),
        )
        return self._enriquecer_pedido(atualizado)

    def _preparar_alteracoes_pedido(
        self,
        pedido: dict[str, Any],
        edicao: dict[str, Any],
        valor_padrao: float | None,
    ) -> dict[str, Any]:
        alteracoes: dict[str, Any] = {}

        preco = self._converter_valor(edicao.get("preco_venda"))
        if preco is None and not edicao and valor_padrao is not None:
            preco = valor_padrao
        if preco is not None:
            alteracoes["preco_venda"] = preco

        custo = self._converter_valor(edicao.get("custo_compra"))
        if custo is not None:
            alteracoes["custo_compra"] = custo

        quantidade = self._converter_numero(edicao.get("quantidade"))
        if quantidade is not None:
            alteracoes["quantidade"] = quantidade

        atributos = self._atributos_edicao(edicao.get("atributos"))
        produto = edicao.get("produto")
        if produto:
            alteracoes["produto"] = str(produto)

        if atributos:
            alteracoes["atributos"] = atributos
            if "produto" not in alteracoes:
                produto_atualizado = self._produto_com_atributos(pedido, atributos)
                if produto_atualizado:
                    alteracoes["produto"] = produto_atualizado

        return alteracoes

    def _atributos_edicao(self, atributos: Any) -> dict[str, list[str]]:
        if not isinstance(atributos, dict):
            return {}

        normalizados: dict[str, list[str]] = {}
        for campo in ("categoria", "cor", "detalhe", "tamanho"):
            valor = atributos.get(campo)
            if isinstance(valor, list):
                valores = [str(item) for item in valor if item]
            elif valor:
                valores = [str(valor)]
            else:
                valores = []

            if valores:
                normalizados[campo] = valores

        return normalizados

    def _produto_com_atributos(
        self,
        pedido: dict[str, Any],
        atributos: dict[str, list[str]],
    ) -> str | None:
        categoria = self._primeiro_atributo_editado(pedido, atributos, "categoria")
        if not categoria:
            return None

        partes = [
            categoria,
            self._primeiro_atributo_editado(pedido, atributos, "cor"),
        ]
        detalhe = self._primeiro_atributo_editado(pedido, atributos, "detalhe")
        if detalhe:
            partes.append(detalhe)
        partes.append(self._primeiro_atributo_editado(pedido, atributos, "tamanho"))

        return " ".join(parte for parte in partes if parte)

    def _primeiro_atributo_editado(
        self,
        pedido: dict[str, Any],
        atributos: dict[str, list[str]],
        campo: str,
    ) -> str | None:
        valores = atributos.get(campo) or []
        if valores:
            return str(valores[0])

        valor_atual = pedido.get(campo)
        return str(valor_atual) if valor_atual else None

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

    def _concluir_pedido(
        self,
        pedido: dict[str, Any],
        valor_informado: float | None,
    ) -> dict[str, Any] | None:
        valor_final = self._valor_final_para_conclusao(pedido, valor_informado)
        if valor_final is not None and valor_final > 0:
            pedido = self._registrar_pagamento_pedido(pedido, valor_final) or pedido

        pedido = self._enriquecer_pedido(pedido) or pedido
        if pedido.get("valor_restante") and float(pedido["valor_restante"]) > 0:
            pedido["tipo_resultado"] = "pedido_pagamento_pendente"
            return pedido

        return self._registrar_entrega_pedido(pedido)

    def _registrar_pagamento_pedido(
        self,
        pedido: dict[str, Any],
        valor_pago: float,
    ) -> dict[str, Any] | None:
        preco_venda = pedido.get("preco_venda")
        if preco_venda is None:
            preco_venda = valor_pago

        valor_pago_total = float(pedido.get("valor_pago") or 0) + float(valor_pago)
        status = self._status_apos_pagamento(
            pedido=pedido,
            preco_venda=float(preco_venda) if preco_venda is not None else None,
            valor_pago_total=valor_pago_total,
        )

        atualizado = self.repository.atualizar_pagamento(
            pedido_id=int(pedido["pedido_id"]),
            preco_venda=float(preco_venda) if preco_venda is not None else None,
            valor_pago_total=valor_pago_total,
            status=status,
        )
        return self._enriquecer_pedido(atualizado)

    def _registrar_entrega_pedido(
        self,
        pedido: dict[str, Any],
    ) -> dict[str, Any] | None:
        pedido = self._enriquecer_pedido(pedido) or pedido
        status = self._status_apos_entrega(pedido)
        atualizado = self.repository.atualizar_entrega(
            pedido_id=int(pedido["pedido_id"]),
            status=status,
        )
        return self._enriquecer_pedido(atualizado)

    def _status_apos_pagamento(
        self,
        pedido: dict[str, Any],
        preco_venda: float | None,
        valor_pago_total: float,
    ) -> str:
        entregue = bool(pedido.get("entregue_em")) or pedido.get("status") == "entregue"
        if preco_venda is not None and valor_pago_total >= preco_venda:
            return "concluido" if entregue else "pago"

        return "entregue" if entregue else "pago_parcial"

    def _status_apos_entrega(self, pedido: dict[str, Any]) -> str:
        preco = pedido.get("preco_venda")
        if preco is None:
            return "entregue"

        valor_restante = float(pedido.get("valor_restante") or 0)
        if valor_restante <= 0:
            return "concluido"

        return "entregue"

    def _enriquecer_pedido(
        self,
        pedido: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not pedido or pedido.get("tipo_resultado") != "pedido":
            return pedido

        preco = pedido.get("preco_venda")
        custo = pedido.get("custo_compra")
        valor_pago = pedido.get("valor_pago")

        if preco is not None:
            pedido["valor_restante"] = max(float(preco) - float(valor_pago or 0), 0)
            pedido["pago_total"] = pedido["valor_restante"] <= 0
        else:
            pedido["pago_total"] = False

        if preco is not None and custo is not None:
            pedido["lucro"] = float(preco) - float(custo)

        pedido["entregue"] = bool(pedido.get("entregue_em"))
        pedido["proxima_etapa"] = self._proxima_etapa(pedido)

        return pedido

    def _proxima_etapa(self, pedido: dict[str, Any]) -> str:
        if pedido.get("status") == "cancelado":
            return "pedido_cancelado"

        if pedido.get("status") == "concluido":
            return "pedido_concluido"

        if pedido.get("custo_compra") is None:
            return "comprar_peca"

        if pedido.get("preco_venda") is None:
            return "definir_preco_de_venda"

        if not pedido.get("pago_total"):
            return "receber_pagamento"

        if not pedido.get("entregue"):
            return "entregar_peca"

        return "concluir_pedido"

    def _produto_contextual(
        self,
        intencao: str,
        cliente: str | None,
        produto: str | None,
        entidades: dict[str, Any],
    ) -> str | None:
        if intencao not in {
            "pedidos_registrar_pagamento",
            "pedidos_entregar",
            "pedidos_concluir",
            "pedidos_confirmar",
            "pedidos_editar",
            "pedidos_cancelar",
            "pedidos_historico",
        }:
            return produto

        if not cliente:
            return produto

        if intencao == "pedidos_editar":
            return None

        if entidades.get("categorias_roupa"):
            return produto

        return None

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

    def _converter_pedido_id(self, valor: Any) -> int | None:
        if valor is None:
            return None

        try:
            pedido_id = int(float(str(valor).replace(",", ".")))
        except (TypeError, ValueError):
            return None

        return pedido_id if pedido_id > 0 else None
