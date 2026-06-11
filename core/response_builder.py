"""
Construtor de respostas do Cooper.

Transforma os dicionarios internos produzidos pelos agentes em mensagens
legiveis para a CLI ou para uma futura interface.
"""

from typing import Any


class ResponseBuilder:
    """Constroi respostas finais a partir do formato padrao interno."""

    CAMPOS_INTERNOS = {
        "mensagem_original",
        "entidades",
        "proximas_acoes",
    }

    def construir(self, resultado: dict[str, Any]) -> str:
        """
        Constroi uma mensagem final com base no resultado interno recebido.

        Args:
            resultado: Dicionario padronizado produzido por agente ou roteador.

        Returns:
            Texto final pronto para exibicao.
        """
        if not isinstance(resultado, dict):
            return "Nao consegui interpretar a resposta interna do Cooper."

        status = resultado.get("status", "indefinido")
        tipo = resultado.get("tipo", "desconhecido")
        erro = resultado.get("erro")
        dados = resultado.get("dados") or {}

        if status == "erro":
            return self._construir_erro(erro=erro)

        if status == "nao_processado":
            return self._construir_nao_processado()

        if dados:
            return self._construir_com_dados(tipo=tipo, dados=dados)

        return f"Operacao '{tipo}' concluida."

    def _construir_com_dados(self, tipo: str, dados: dict[str, Any]) -> str:
        """Constroi uma resposta textual quando ha dados estruturados."""
        linhas = [self._titulo_operacao(tipo), ""]

        resumo = dados.get("resumo")
        if resumo:
            linhas.append(str(resumo))

        resultado = dados.get("resultado")
        if resultado is not None:
            linhas.extend(self._formatar_resultado(resultado))

        campos_necessarios = dados.get("campos_necessarios") or []
        if campos_necessarios:
            linhas.append("")
            linhas.append("Para continuar, preciso de:")
            linhas.extend(f"- {campo}" for campo in campos_necessarios)

        return "\n".join(linhas).strip()

    def _titulo_operacao(self, tipo: str) -> str:
        return f"Operacao: {tipo}"

    def _formatar_resultado(self, resultado: Any) -> list[str]:
        if isinstance(resultado, dict) and "tipo_relatorio" in resultado:
            return self._formatar_relatorio(resultado)

        if isinstance(resultado, dict) and resultado.get("tipo_resultado") == "precificacao":
            return self._formatar_precificacao(resultado)

        if isinstance(resultado, dict) and "itens" in resultado:
            return self._formatar_inventario(resultado.get("itens") or [])

        if isinstance(resultado, dict):
            return self._formatar_resultado_dict(resultado)

        return ["", f"Resultado: {resultado}"]

    def _formatar_precificacao(self, resultado: dict[str, Any]) -> list[str]:
        margem = float(resultado.get("margem_percentual") or 0) * 100
        multiplicador = resultado.get("multiplicador")
        linhas = [
            "",
            f"Produto: {resultado.get('produto')}",
            f"Custo total: {self._formatar_moeda(resultado.get('custo_total'))}",
        ]

        if multiplicador:
            linhas.append(f"Regra usada: {self._formatar_numero(multiplicador)}x o custo")
        else:
            linhas.append(f"Margem usada: {self._formatar_numero(margem)}%")

        taxa = resultado.get("taxa_operacional")
        if taxa:
            linhas.append(f"Taxa operacional: {self._formatar_moeda(taxa)}")

        linhas.extend(
            [
                f"Preco sugerido: {self._formatar_moeda(resultado.get('preco_sugerido'))}",
                f"Reembolso/lucro estimado: {self._formatar_moeda(resultado.get('lucro_sugerido'))}",
            ]
        )

        return linhas

    def _formatar_relatorio(self, resultado: dict[str, Any]) -> list[str]:
        tipo = resultado.get("tipo_relatorio")

        if tipo == "vendas_periodo":
            return self._formatar_relatorio_vendas(resultado)

        if tipo == "estoque_baixo":
            return self._formatar_relatorio_estoque_baixo(resultado)

        if tipo == "historico_produto":
            return self._formatar_relatorio_historico(resultado)

        if tipo in {"pedidos_pendentes", "pedidos_concluidos", "compras_pendentes"}:
            return self._formatar_relatorio_pedidos(resultado)

        if tipo == "financeiro_pedidos":
            return self._formatar_relatorio_financeiro_pedidos(resultado)

        if tipo == "contas_resumo":
            return self._formatar_contas(resultado)

        return ["", f"Relatorio: {resultado}"]

    def _formatar_relatorio_vendas(self, resultado: dict[str, Any]) -> list[str]:
        periodo = resultado.get("periodo", "periodo")
        linhas = ["", f"Vendas de {periodo}:"]
        linhas.append(f"- Vendas: {self._formatar_numero(resultado.get('total_vendas'))}")
        linhas.append(
            f"- Pecas vendidas: {self._formatar_numero(resultado.get('quantidade_itens'))}"
        )
        linhas.append(f"- Total: {self._formatar_moeda(resultado.get('valor_total'))}")

        itens = resultado.get("itens") or []
        if itens:
            linhas.append("")
            linhas.append("Produtos vendidos:")
            for item in itens:
                produto = item.get("produto", "produto sem nome")
                quantidade = self._formatar_numero(item.get("quantidade_itens"))
                valor = self._formatar_moeda(item.get("valor_total"))
                linhas.append(f"- {produto}: {quantidade} pecas, {valor}")

        return linhas

    def _formatar_relatorio_pedidos(self, resultado: dict[str, Any]) -> list[str]:
        tipo = resultado.get("tipo_relatorio")
        titulo = "Pedidos pendentes"
        if tipo == "compras_pendentes":
            titulo = "Compras pendentes"
        if tipo == "pedidos_concluidos":
            titulo = "Pedidos concluidos"

        itens = resultado.get("itens") or []
        if not itens:
            return ["", f"{titulo}: nenhum."]

        linhas = ["", f"{titulo}:"]
        for pedido in itens:
            linhas.append(f"- {self._resumo_pedido(pedido)}")

        return linhas

    def _formatar_relatorio_financeiro_pedidos(
        self,
        resultado: dict[str, Any],
    ) -> list[str]:
        return [
            "",
            "Financeiro dos pedidos:",
            f"- Pedidos: {self._formatar_numero(resultado.get('total_pedidos'))}",
            f"- Valor a receber: {self._formatar_moeda(resultado.get('valor_a_receber'))}",
            f"- Valor recebido: {self._formatar_moeda(resultado.get('valor_recebido'))}",
            f"- Custos realizados: {self._formatar_moeda(resultado.get('custos_realizados'))}",
            f"- Lucro conhecido: {self._formatar_moeda(resultado.get('lucro_conhecido'))}",
            f"- Lucro realizado: {self._formatar_moeda(resultado.get('lucro_realizado'))}",
        ]

    def _formatar_contas(self, resultado: dict[str, Any]) -> list[str]:
        visao = resultado.get("visao")
        linhas = ["", "Contas:"]

        if visao in {None, "resumo"}:
            linhas.append(
                f"- Pedidos: {self._formatar_numero(resultado.get('total_pedidos'))}"
            )
            linhas.append(
                f"- Contas avulsas: {self._formatar_numero(resultado.get('total_contas'))}"
            )

        if visao in {None, "resumo", "a_receber"}:
            linhas.append(
                f"- Valor a receber: {self._formatar_moeda(resultado.get('valor_a_receber'))}"
            )

        if visao in {None, "resumo"}:
            linhas.append(
                f"- Valor recebido: {self._formatar_moeda(resultado.get('valor_recebido'))}"
            )
            linhas.append(
                f"- Custos realizados: {self._formatar_moeda(resultado.get('custos_realizados'))}"
            )

        if visao in {None, "resumo", "lucro"}:
            linhas.append(
                f"- Lucro conhecido: {self._formatar_moeda(resultado.get('lucro_conhecido'))}"
            )
            linhas.append(
                f"- Lucro realizado: {self._formatar_moeda(resultado.get('lucro_realizado'))}"
            )

        return linhas

    def _formatar_relatorio_estoque_baixo(
        self,
        resultado: dict[str, Any],
    ) -> list[str]:
        limite = self._formatar_numero(resultado.get("limite"))
        itens = resultado.get("itens") or []

        if not itens:
            return ["", f"Nenhum produto com estoque ate {limite}."]

        linhas = ["", f"Produtos com estoque ate {limite}:"]
        for item in itens:
            produto = item.get("produto", "produto sem nome")
            quantidade = self._formatar_numero(item.get("quantidade"))
            atributos = self._formatar_atributos(item)
            descricao = produto
            if atributos:
                descricao = f"{descricao} ({atributos})"
            linhas.append(f"- {descricao}: {quantidade}")

        return linhas

    def _formatar_relatorio_historico(self, resultado: dict[str, Any]) -> list[str]:
        historico = resultado.get("historico")
        produto_consultado = resultado.get("produto_consultado", "produto")

        if not historico:
            return ["", f"Nao encontrei historico para {produto_consultado}."]

        produto = historico.get("produto") or {}
        movimentos = historico.get("movimentos") or []
        descricao = produto.get("produto", produto_consultado)
        atributos = self._formatar_atributos(produto)
        if atributos:
            descricao = f"{descricao} ({atributos})"

        linhas = ["", f"Historico de {descricao}:"]
        if not movimentos:
            linhas.append("- Nenhum movimento registrado.")
            return linhas

        for movimento in movimentos:
            tipo = str(movimento.get("tipo", "movimento")).capitalize()
            quantidade = self._formatar_numero(movimento.get("quantidade"))
            anterior = self._formatar_numero(movimento.get("quantidade_anterior"))
            atual = self._formatar_numero(movimento.get("quantidade_atual"))
            linhas.append(f"- {tipo}: {quantidade} | {anterior} -> {atual}")

        return linhas

    def _formatar_resultado_dict(self, resultado: dict[str, Any]) -> list[str]:
        linhas = [""]

        produto = resultado.get("produto")
        pedido_id = resultado.get("pedido_id")
        conta_id = resultado.get("conta_id")
        cliente = resultado.get("cliente")
        descricao = resultado.get("descricao")
        status = resultado.get("status")
        preco_venda = resultado.get("preco_venda")
        custo_compra = resultado.get("custo_compra")
        valor_total = resultado.get("valor_total")
        valor_pago = resultado.get("valor_pago")
        valor_restante = resultado.get("valor_restante")
        lucro = resultado.get("lucro")
        sugestao_preco = resultado.get("sugestao_preco")
        quantidade = resultado.get("quantidade")
        quantidade_atual = resultado.get("quantidade_atual")
        movimento_realizado = resultado.get("movimento_realizado")
        motivo = resultado.get("motivo")
        venda_realizada = resultado.get("venda_realizada")

        if resultado.get("tipo_resultado") == "pedido_nao_encontrado":
            linhas.append("Pedido nao encontrado.")
            if cliente:
                linhas.append(f"Cliente: {cliente}")
            if produto:
                linhas.append(f"Produto: {produto}")
            return linhas

        if resultado.get("tipo_resultado") == "conta_nao_encontrada":
            linhas.append("Nao encontrei conta em aberto para esse cliente.")
            if cliente:
                linhas.append(f"Cliente: {cliente}")
            return linhas

        if resultado.get("tipo_resultado") == "conta_resumo_cliente":
            linhas.append(f"Cliente: {cliente}")
            linhas.append(f"Valor total em aberto: {self._formatar_moeda(valor_total)}")
            linhas.append(f"Valor pago: {self._formatar_moeda(valor_pago)}")
            linhas.append(f"Falta pagar: {self._formatar_moeda(valor_restante)}")
            return linhas

        if resultado.get("tipo_resultado") == "pedido_precisa_valor":
            linhas.append("Encontrei o pedido, mas ainda falta o valor de venda.")
            linhas.append("Diga, por exemplo: vendi pra cliente por R$ 20.")

        if pedido_id:
            linhas.append(f"Pedido #{pedido_id}")

        if conta_id:
            linhas.append(f"Conta #{conta_id}")

        if cliente:
            linhas.append(f"Cliente: {cliente}")

        if produto:
            linhas.append(f"Produto: {produto}")

        if descricao:
            linhas.append(f"Descricao: {descricao}")

        atributos = self._formatar_atributos(resultado)
        if atributos:
            linhas.append(f"Variacao: {atributos}")

        if quantidade is not None and quantidade_atual is None:
            if resultado.get("tipo_resultado") == "pedido":
                linhas.append(f"Quantidade: {self._formatar_numero(quantidade)}")
            else:
                linhas.append(f"Saldo: {self._formatar_numero(quantidade)}")

        if status:
            linhas.append(f"Status: {status}")

        if preco_venda is not None:
            linhas.append(f"Preco de venda: {self._formatar_moeda(preco_venda)}")

        if valor_total is not None:
            linhas.append(f"Valor total: {self._formatar_moeda(valor_total)}")

        if custo_compra is not None:
            linhas.append(f"Custo de compra: {self._formatar_moeda(custo_compra)}")

        if valor_pago is not None:
            linhas.append(f"Valor pago: {self._formatar_moeda(valor_pago)}")

        if valor_restante is not None:
            linhas.append(f"Falta pagar: {self._formatar_moeda(valor_restante)}")

        if lucro is not None:
            linhas.append(f"Lucro: {self._formatar_moeda(lucro)}")

        if sugestao_preco:
            linhas.append(
                "Preco de venda sugerido: "
                f"{self._formatar_moeda(sugestao_preco.get('preco_sugerido'))}"
            )
            linhas.append(
                "Lucro estimado: "
                f"{self._formatar_moeda(sugestao_preco.get('lucro_sugerido'))}"
            )

        if quantidade_atual is not None:
            linhas.append(f"Saldo atual: {self._formatar_numero(quantidade_atual)}")

        if movimento_realizado is True:
            movimento = resultado.get("movimento_tipo", "movimento")
            quantidade_movimentada = resultado.get("quantidade_movimentada")
            linhas.append(
                f"{movimento.capitalize()} registrada: "
                f"{self._formatar_numero(quantidade_movimentada)}"
            )

        if movimento_realizado is False:
            linhas.append("Movimento nao realizado.")
            if motivo:
                linhas.append(f"Motivo: {motivo}")

        if venda_realizada is True:
            quantidade_vendida = resultado.get("quantidade_vendida")
            valor = resultado.get("valor")
            linhas.append(f"Venda registrada: {self._formatar_numero(quantidade_vendida)}")
            if valor is not None:
                linhas.append(f"Valor: R$ {self._formatar_numero(valor)}")

            estoque = resultado.get("estoque") or {}
            saldo_atual = estoque.get("quantidade_atual")
            if saldo_atual is not None:
                linhas.append(f"Saldo apos venda: {self._formatar_numero(saldo_atual)}")

        if venda_realizada is False:
            linhas.append("Venda nao realizada.")
            if motivo:
                linhas.append(f"Motivo: {motivo}")

        sku = resultado.get("sku")
        if sku:
            linhas.append(f"SKU: {sku}")

        return linhas

    def _resumo_pedido(self, pedido: dict[str, Any]) -> str:
        partes = [
            f"#{pedido.get('pedido_id')}",
            str(pedido.get("cliente")),
            str(pedido.get("produto")),
            f"status {pedido.get('status')}",
        ]
        preco = pedido.get("preco_venda")
        custo = pedido.get("custo_compra")
        valor_pago = pedido.get("valor_pago")
        valor_restante = pedido.get("valor_restante")
        if preco is not None:
            partes.append(f"venda {self._formatar_moeda(preco)}")
        if custo is not None:
            partes.append(f"custo {self._formatar_moeda(custo)}")
        if valor_pago is not None:
            partes.append(f"pago {self._formatar_moeda(valor_pago)}")
        if valor_restante:
            partes.append(f"falta {self._formatar_moeda(valor_restante)}")
        return " | ".join(partes)

    def _formatar_inventario(self, itens: list[dict[str, Any]]) -> list[str]:
        if not itens:
            return ["", "Inventario vazio."]

        linhas = ["", "Inventario:"]
        for item in itens:
            produto = item.get("produto")
            quantidade = self._formatar_numero(item.get("quantidade"))
            atributos = self._formatar_atributos(item)
            descricao = produto or "produto sem nome"
            if atributos:
                descricao = f"{descricao} ({atributos})"
            linhas.append(f"- {descricao}: {quantidade}")

        return linhas

    def _formatar_atributos(self, dados: dict[str, Any]) -> str:
        partes = []
        for campo in ("categoria", "cor", "detalhe", "tamanho"):
            valor = dados.get(campo)
            if valor:
                partes.append(str(valor))
        return " / ".join(partes)

    def _formatar_numero(self, valor: Any) -> str:
        if valor is None:
            return "0"
        if isinstance(valor, float) and valor.is_integer():
            return str(int(valor))
        return str(valor)

    def _formatar_moeda(self, valor: Any) -> str:
        try:
            numero = float(valor or 0)
        except (TypeError, ValueError):
            numero = 0

        if numero.is_integer():
            return f"R$ {int(numero)}"

        return f"R$ {numero:.2f}"

    def _construir_com_dados_debug(self, tipo: str, dados: dict[str, Any]) -> str:
        linhas = [f"Operacao: {tipo}", ""]

        for chave, valor in dados.items():
            if chave in self.CAMPOS_INTERNOS:
                continue
            nome_campo = str(chave).replace("_", " ").capitalize()
            linhas.extend(self._formatar_campo(nome_campo, valor))

        return "\n".join(linhas).strip()

    def _formatar_campo(self, nome_campo: str, valor: Any) -> list[str]:
        """Formata campos simples e colecoes para leitura na CLI."""
        if isinstance(valor, list):
            if not valor:
                return [f"{nome_campo}: nenhum"]

            linhas = [f"{nome_campo}:"]
            linhas.extend(f"- {item}" for item in valor)
            return linhas

        if isinstance(valor, dict):
            if not valor:
                return [f"{nome_campo}: nenhum"]

            linhas = [f"{nome_campo}:"]
            for chave, item in valor.items():
                linhas.append(f"- {chave}: {item}")
            return linhas

        return [f"{nome_campo}: {valor}"]

    def _construir_erro(self, erro: str | None = None) -> str:
        """Constroi uma resposta textual para cenarios de erro."""
        if erro:
            return f"Erro: {erro}"

        return "Ocorreu um erro durante o processamento."

    def _construir_nao_processado(self) -> str:
        """Constroi uma resposta textual quando nenhum agente atende."""
        return (
            "Ainda nao sei qual area deve cuidar dessa solicitacao. "
            "Por favor, reformule sua pergunta."
        )

    def construir_debug(self, resultado: dict[str, Any]) -> str:
        """Constroi uma resposta detalhada para depuracao interna."""
        if not isinstance(resultado, dict):
            return "Resultado invalido para depuracao."

        return (
            f"Agente: {resultado.get('agente')}\n"
            f"Status: {resultado.get('status')}\n"
            f"Tipo: {resultado.get('tipo')}\n"
            f"Dados: {resultado.get('dados')}\n"
            f"Erro: {resultado.get('erro')}"
        )
