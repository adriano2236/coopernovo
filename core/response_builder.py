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

        if isinstance(resultado, dict) and str(
            resultado.get("tipo_resultado", "")
        ).startswith("memoria"):
            return self._formatar_memoria(resultado)

        if isinstance(resultado, dict) and str(
            resultado.get("tipo_resultado", "")
        ).startswith(("backup", "exportacao")):
            return self._formatar_backup_exportacao(resultado)

        if (
            isinstance(resultado, dict)
            and resultado.get("tipo_resultado") == "busca_resultados"
        ):
            return self._formatar_busca(resultado)

        if isinstance(resultado, dict) and str(
            resultado.get("tipo_resultado", "")
        ).startswith("cliente"):
            return self._formatar_cliente(resultado)

        if isinstance(resultado, dict) and str(
            resultado.get("tipo_resultado", "")
        ).startswith("fornecedor"):
            return self._formatar_fornecedor(resultado)

        if isinstance(resultado, dict) and resultado.get("tipo_resultado") == "precificacao":
            return self._formatar_precificacao(resultado)

        if isinstance(resultado, dict) and str(
            resultado.get("tipo_resultado", "")
        ).startswith(("caixa", "despesa")):
            return self._formatar_caixa_despesa(resultado)

        if (
            isinstance(resultado, dict)
            and resultado.get("tipo_resultado") == "pedido_historico"
        ):
            return self._formatar_historico_pedido(resultado)

        if isinstance(resultado, dict) and "itens" in resultado:
            return self._formatar_inventario(resultado.get("itens") or [])

        if isinstance(resultado, dict):
            return self._formatar_resultado_dict(resultado)

        return ["", f"Resultado: {resultado}"]

    def _formatar_memoria(self, resultado: dict[str, Any]) -> list[str]:
        tipo = resultado.get("tipo_resultado")

        if tipo == "memoria":
            return [
                "",
                f"Memoria #{resultado.get('memoria_id')}",
                f"Fase: {resultado.get('fase')}",
                f"Tipo: {resultado.get('tipo_memoria')}",
                f"Chave: {resultado.get('chave')}",
                f"Valor: {resultado.get('valor')}",
            ]

        if tipo == "memoria_lista":
            itens = resultado.get("itens") or []
            titulo = resultado.get("titulo") or "Memorias"
            if not itens:
                return ["", f"{titulo}: nenhuma."]

            linhas = ["", f"{titulo}:"]
            for item in itens:
                linhas.append(
                    "- "
                    f"#{item.get('memoria_id')} | "
                    f"fase {item.get('fase')} | "
                    f"{item.get('tipo_memoria')} | "
                    f"{item.get('valor')}"
                )
            return linhas

        if tipo == "memoria_historico":
            itens = resultado.get("itens") or []
            if not itens:
                return ["", "Historico de conversa vazio."]

            linhas = ["", "Historico recente:"]
            for item in itens:
                agente = item.get("agente") or "sem agente"
                intencao = item.get("intencao") or "sem intencao"
                texto = item.get("texto") or ""
                linhas.append(f"- {agente} / {intencao}: {texto}")
            return linhas

        if tipo == "memoria_esquecida":
            itens = resultado.get("itens") or []
            if not itens:
                return ["", "Nao encontrei memoria ativa com esse termo."]

            linhas = ["", "Memorias removidas:"]
            for item in itens:
                linhas.append(f"- #{item.get('memoria_id')}: {item.get('valor')}")
            return linhas

        return ["", f"Memoria: {resultado}"]

    def _formatar_backup_exportacao(self, resultado: dict[str, Any]) -> list[str]:
        tipo = resultado.get("tipo_resultado")

        if tipo == "backup_nao_encontrado":
            return [
                "",
                "Banco de dados nao encontrado.",
                f"Origem esperada: {resultado.get('origem')}",
            ]

        if tipo == "backup_arquivo":
            return [
                "",
                "Backup criado:",
                f"Arquivo: {resultado.get('caminho')}",
                f"Origem: {resultado.get('origem')}",
                f"Tamanho: {self._formatar_bytes(resultado.get('tamanho_bytes'))}",
            ]

        if tipo == "exportacao_arquivo":
            linhas = [
                "",
                "Exportacao criada:",
                f"Formato: {resultado.get('formato')}",
                f"Caminho: {resultado.get('caminho')}",
                f"Tabelas: {self._formatar_numero(resultado.get('total_tabelas'))}",
                f"Registros: {self._formatar_numero(resultado.get('total_registros'))}",
            ]
            if resultado.get("tamanho_bytes") is not None:
                linhas.append(
                    f"Tamanho: {self._formatar_bytes(resultado.get('tamanho_bytes'))}"
                )

            tabelas = resultado.get("tabelas") or []
            if tabelas:
                linhas.append("")
                linhas.append("Conteudo:")
                for tabela in tabelas:
                    linhas.append(
                        f"- {tabela.get('nome')}: "
                        f"{self._formatar_numero(tabela.get('total_registros'))} registros"
                    )

            arquivos = resultado.get("arquivos") or []
            if arquivos:
                linhas.append("")
                linhas.append("Arquivos:")
                for arquivo in arquivos[:8]:
                    linhas.append(f"- {arquivo}")
                if len(arquivos) > 8:
                    linhas.append(f"- ... mais {len(arquivos) - 8} arquivos")

            return linhas

        if tipo == "backup_lista":
            linhas = [
                "",
                "Backups e exportacoes:",
                f"- Backups: {self._formatar_numero(resultado.get('total_backups'))}",
                f"- Exportacoes: {self._formatar_numero(resultado.get('total_exportacoes'))}",
            ]
            backups = resultado.get("backups") or []
            exportacoes = resultado.get("exportacoes") or []

            if backups:
                linhas.append("")
                linhas.append("Backups recentes:")
                for item in backups[:10]:
                    tamanho = self._formatar_bytes(item.get("tamanho_bytes"))
                    linhas.append(f"- {item.get('nome')} | {tamanho} | {item.get('caminho')}")

            if exportacoes:
                linhas.append("")
                linhas.append("Exportacoes recentes:")
                for item in exportacoes[:10]:
                    tipo_arquivo = item.get("tipo_arquivo")
                    tamanho = self._formatar_bytes(item.get("tamanho_bytes"))
                    linhas.append(
                        f"- {item.get('nome')} | {tipo_arquivo} | {tamanho} | "
                        f"{item.get('caminho')}"
                    )

            if not backups and not exportacoes:
                linhas.append("- Nenhum arquivo criado ainda.")

            return linhas

        return ["", f"Backup/exportacao: {resultado}"]

    def _formatar_busca(self, resultado: dict[str, Any]) -> list[str]:
        termo = resultado.get("termo") or "termo informado"
        total = int(resultado.get("total") or 0)
        linhas = ["", f"Busca por: {termo}"]

        if total <= 0:
            linhas.append("Nenhum resultado encontrado.")
            return linhas

        clientes = resultado.get("clientes") or []
        if clientes:
            linhas.append("")
            linhas.append("Clientes:")
            for cliente in clientes:
                linha = (
                    f"- #{cliente.get('cliente_id')} | "
                    f"{cliente.get('cliente')}"
                )
                if cliente.get("telefone"):
                    linha += f" | telefone {cliente.get('telefone')}"
                if cliente.get("endereco"):
                    linha += f" | {cliente.get('endereco')}"
                linhas.append(linha)

        pedidos = resultado.get("pedidos") or []
        if pedidos:
            linhas.append("")
            linhas.append("Pedidos:")
            for pedido in pedidos:
                linhas.append(f"- {self._resumo_pedido(pedido)}")

        fornecedores = resultado.get("fornecedores") or []
        if fornecedores:
            linhas.append("")
            linhas.append("Fornecedores:")
            for fornecedor in fornecedores:
                linha = (
                    f"- #{fornecedor.get('fornecedor_id')} | "
                    f"{fornecedor.get('fornecedor')}"
                )
                if fornecedor.get("telefone"):
                    linha += f" | telefone {fornecedor.get('telefone')}"
                if fornecedor.get("endereco"):
                    linha += f" | {fornecedor.get('endereco')}"
                linhas.append(linha)

        produtos_estoque = resultado.get("produtos_estoque") or []
        if produtos_estoque:
            linhas.append("")
            linhas.append("Produtos em estoque:")
            for produto in produtos_estoque:
                descricao = produto.get("produto") or "produto sem nome"
                atributos = self._formatar_atributos(produto)
                if atributos:
                    descricao = f"{descricao} ({atributos})"
                saldo = self._formatar_numero(produto.get("quantidade"))
                linhas.append(f"- #{produto.get('produto_id')} | {descricao} | saldo {saldo}")

        produtos_fornecedor = resultado.get("produtos_fornecedor") or []
        if produtos_fornecedor:
            linhas.append("")
            linhas.append("Produtos de fornecedores:")
            for produto in produtos_fornecedor:
                linha = (
                    f"- #{produto.get('produto_fornecedor_id')} | "
                    f"{produto.get('produto')} | "
                    f"{produto.get('fornecedor')}"
                )
                if produto.get("ultimo_custo") is not None:
                    linha += (
                        " | ultimo custo "
                        f"{self._formatar_moeda(produto.get('ultimo_custo'))}"
                    )
                linhas.append(linha)

        return linhas

    def _formatar_cliente(self, resultado: dict[str, Any]) -> list[str]:
        tipo = resultado.get("tipo_resultado")

        if tipo == "cliente_nao_encontrado":
            return [
                "",
                "Cliente nao encontrado.",
                f"Cliente: {resultado.get('cliente')}",
            ]

        if tipo == "clientes_lista":
            itens = resultado.get("itens") or []
            if not itens:
                return ["", "Clientes cadastrados: nenhum."]

            linhas = ["", "Clientes cadastrados:"]
            for cliente in itens:
                telefone = cliente.get("telefone") or "sem telefone"
                endereco = cliente.get("endereco") or "sem endereco"
                linhas.append(
                    f"- #{cliente.get('cliente_id')} | "
                    f"{cliente.get('cliente')} | {telefone} | {endereco}"
                )
            return linhas

        if tipo == "cliente":
            linhas = [
                "",
                f"Cliente #{resultado.get('cliente_id')}",
                f"Nome: {resultado.get('cliente')}",
            ]
            if resultado.get("telefone"):
                linhas.append(f"Telefone: {resultado.get('telefone')}")
            if resultado.get("endereco"):
                linhas.append(f"Endereco: {resultado.get('endereco')}")
            if resultado.get("observacoes"):
                linhas.append(f"Observacoes: {resultado.get('observacoes')}")
            return linhas

        return ["", f"Cliente: {resultado}"]

    def _formatar_fornecedor(self, resultado: dict[str, Any]) -> list[str]:
        tipo = resultado.get("tipo_resultado")

        if tipo == "fornecedor_nao_encontrado":
            return [
                "",
                "Fornecedor nao encontrado.",
                f"Fornecedor: {resultado.get('fornecedor')}",
            ]

        if tipo == "fornecedores_lista":
            itens = resultado.get("itens") or []
            if not itens:
                return ["", "Fornecedores cadastrados: nenhum."]

            linhas = ["", "Fornecedores cadastrados:"]
            for fornecedor in itens:
                telefone = fornecedor.get("telefone") or "sem telefone"
                endereco = fornecedor.get("endereco") or "sem endereco"
                linhas.append(
                    f"- #{fornecedor.get('fornecedor_id')} | "
                    f"{fornecedor.get('fornecedor')} | {telefone} | {endereco}"
                )
            return linhas

        if tipo == "fornecedores_produto_lista":
            itens = resultado.get("itens") or []
            produto = resultado.get("produto") or "produto"
            if not itens:
                return ["", f"Nao encontrei fornecedor para {produto}."]

            linhas = ["", f"Fornecedores para {produto}:"]
            for item in itens:
                linha = f"- {item.get('fornecedor')}"
                if item.get("ultimo_custo") is not None:
                    linha += f" | ultimo custo {self._formatar_moeda(item.get('ultimo_custo'))}"
                if item.get("telefone"):
                    linha += f" | telefone {item.get('telefone')}"
                linhas.append(linha)
            return linhas

        if tipo == "fornecedor_produto":
            linhas = [
                "",
                "Produto do fornecedor registrado.",
                f"Fornecedor: {resultado.get('fornecedor')}",
                f"Produto: {resultado.get('produto')}",
            ]
            atributos = self._formatar_atributos(resultado)
            if atributos:
                linhas.append(f"Variacao: {atributos}")
            if resultado.get("ultimo_custo") is not None:
                linhas.append(
                    f"Ultimo custo: {self._formatar_moeda(resultado.get('ultimo_custo'))}"
                )
            if resultado.get("telefone"):
                linhas.append(f"Telefone: {resultado.get('telefone')}")
            return linhas

        if tipo == "fornecedor":
            linhas = [
                "",
                f"Fornecedor #{resultado.get('fornecedor_id')}",
                f"Nome: {resultado.get('fornecedor')}",
            ]
            if resultado.get("telefone"):
                linhas.append(f"Telefone: {resultado.get('telefone')}")
            if resultado.get("endereco"):
                linhas.append(f"Endereco: {resultado.get('endereco')}")
            if resultado.get("observacoes"):
                linhas.append(f"Observacoes: {resultado.get('observacoes')}")

            produtos = resultado.get("produtos") or []
            if produtos:
                linhas.append("")
                linhas.append("Produtos:")
                for produto in produtos:
                    descricao = produto.get("produto") or "produto sem nome"
                    custo = produto.get("ultimo_custo")
                    if custo is not None:
                        descricao += f" | ultimo custo {self._formatar_moeda(custo)}"
                    linhas.append(f"- {descricao}")
            return linhas

        return ["", f"Fornecedor: {resultado}"]

    def _formatar_caixa_despesa(self, resultado: dict[str, Any]) -> list[str]:
        tipo = resultado.get("tipo_resultado")

        if tipo == "despesa":
            linhas = [
                "",
                f"Despesa #{resultado.get('despesa_id')}",
                f"Descricao: {resultado.get('descricao')}",
                f"Categoria: {resultado.get('categoria') or 'geral'}",
                f"Valor: {self._formatar_moeda(resultado.get('valor'))}",
            ]
            if resultado.get("saldo_caixa") is not None:
                linhas.append(
                    f"Saldo do caixa: {self._formatar_moeda(resultado.get('saldo_caixa'))}"
                )
            return linhas

        if tipo == "despesas_lista":
            itens = resultado.get("itens") or []
            linhas = [
                "",
                "Despesas:",
                f"- Total registrado: {self._formatar_moeda(resultado.get('valor_despesas'))}",
                f"- Quantidade: {self._formatar_numero(resultado.get('total_despesas'))}",
            ]
            if not itens:
                linhas.append("- Nenhuma despesa cadastrada.")
                return linhas

            linhas.append("")
            linhas.append("Ultimas despesas:")
            for item in itens:
                linhas.append(
                    f"- #{item.get('despesa_id')} | "
                    f"{item.get('descricao')} | "
                    f"{self._formatar_moeda(item.get('valor'))}"
                )
            return linhas

        if tipo == "caixa_movimento":
            movimento = resultado.get("movimento_tipo") or "movimento"
            linhas = [
                "",
                f"Caixa #{resultado.get('movimento_id')}",
                f"Tipo: {movimento}",
                f"Descricao: {resultado.get('descricao')}",
                f"Valor: {self._formatar_moeda(resultado.get('valor'))}",
            ]
            if resultado.get("saldo_caixa") is not None:
                linhas.append(
                    f"Saldo do caixa: {self._formatar_moeda(resultado.get('saldo_caixa'))}"
                )
            return linhas

        return ["", f"Financeiro: {resultado}"]

    def _formatar_historico_pedido(self, resultado: dict[str, Any]) -> list[str]:
        pedido = resultado.get("pedido") or {}
        itens = resultado.get("itens") or []
        linhas = [
            "",
            f"Pedido #{pedido.get('pedido_id')}",
            f"Cliente: {pedido.get('cliente')}",
            f"Produto: {pedido.get('produto')}",
            f"Status: {pedido.get('status')}",
        ]

        if pedido.get("preco_venda") is not None:
            linhas.append(f"Preco de venda: {self._formatar_moeda(pedido.get('preco_venda'))}")
        if pedido.get("custo_compra") is not None:
            linhas.append(f"Custo de compra: {self._formatar_moeda(pedido.get('custo_compra'))}")
        if pedido.get("valor_pago") is not None:
            linhas.append(f"Valor pago: {self._formatar_moeda(pedido.get('valor_pago'))}")
        if pedido.get("valor_restante") is not None and pedido.get("status") != "cancelado":
            linhas.append(f"Falta pagar: {self._formatar_moeda(pedido.get('valor_restante'))}")

        linhas.append("")
        linhas.append("Historico:")

        if not itens:
            linhas.append("- Nenhum evento registrado para esse pedido.")
            return linhas

        for item in itens:
            criado = self._formatar_data_curta(item.get("criado_em"))
            descricao = item.get("descricao") or item.get("evento")
            detalhes = self._detalhes_historico_pedido(item.get("dados") or {})
            linha = f"- {criado} | {descricao}"
            if detalhes:
                linha += f" | {detalhes}"
            linhas.append(linha)

        return linhas

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
            linhas.append(
                f"- Despesas: {self._formatar_numero(resultado.get('total_despesas'))}"
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
            linhas.append(
                f"- Despesas registradas: {self._formatar_moeda(resultado.get('valor_despesas'))}"
            )

        if visao in {None, "resumo", "lucro"}:
            linhas.append(
                f"- Lucro conhecido: {self._formatar_moeda(resultado.get('lucro_conhecido'))}"
            )
            linhas.append(
                f"- Lucro realizado: {self._formatar_moeda(resultado.get('lucro_realizado'))}"
            )
            linhas.append(
                f"- Lucro apos despesas: {self._formatar_moeda(resultado.get('lucro_apos_despesas'))}"
            )

        if visao in {None, "resumo", "caixa"}:
            linhas.append(
                f"- Entradas no caixa: {self._formatar_moeda(resultado.get('caixa_entradas'))}"
            )
            linhas.append(
                f"- Saidas do caixa: {self._formatar_moeda(resultado.get('caixa_saidas'))}"
            )
            linhas.append(
                f"- Saldo do caixa: {self._formatar_moeda(resultado.get('caixa_saldo'))}"
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
        proxima_etapa = resultado.get("proxima_etapa")
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
            if pedido_id:
                linhas.append(f"Pedido #{pedido_id}")
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

        if resultado.get("tipo_resultado") == "pedido_pagamento_pendente":
            linhas.append("Pedido ainda tem pagamento pendente.")

        if resultado.get("tipo_resultado") == "pedido_sem_alteracao":
            linhas.append("Nao encontrei uma alteracao clara para aplicar.")

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

        if proxima_etapa:
            linhas.append(f"Proxima etapa: {self._formatar_etapa_pedido(proxima_etapa)}")

        if preco_venda is not None:
            linhas.append(f"Preco de venda: {self._formatar_moeda(preco_venda)}")

        if valor_total is not None:
            linhas.append(f"Valor total: {self._formatar_moeda(valor_total)}")

        if custo_compra is not None:
            linhas.append(f"Custo de compra: {self._formatar_moeda(custo_compra)}")

        if valor_pago is not None:
            linhas.append(f"Valor pago: {self._formatar_moeda(valor_pago)}")

        if valor_restante is not None and status != "cancelado":
            linhas.append(f"Falta pagar: {self._formatar_moeda(valor_restante)}")

        if lucro is not None and status != "cancelado":
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

    def _detalhes_historico_pedido(self, dados: dict[str, Any]) -> str:
        partes = []
        if dados.get("status"):
            partes.append(f"status {dados.get('status')}")
        if dados.get("quantidade") is not None:
            partes.append(f"qtd {self._formatar_numero(dados.get('quantidade'))}")
        if dados.get("preco_venda") is not None:
            partes.append(f"venda {self._formatar_moeda(dados.get('preco_venda'))}")
        if dados.get("custo_compra") is not None:
            partes.append(f"custo {self._formatar_moeda(dados.get('custo_compra'))}")
        if dados.get("valor_pago_total") is not None:
            partes.append(
                f"pago total {self._formatar_moeda(dados.get('valor_pago_total'))}"
            )
        produto = dados.get("produto")
        if produto:
            partes.append(f"produto {produto}")
        return " | ".join(partes)

    def _formatar_data_curta(self, valor: Any) -> str:
        texto = str(valor or "")
        if "T" in texto:
            data, horario = texto.split("T", 1)
            horario = horario.split("+", 1)[0].split(".", 1)[0]
            return f"{data} {horario}"
        return texto or "sem data"

    def _formatar_etapa_pedido(self, etapa: str) -> str:
        etapas = {
            "comprar_peca": "comprar a peca",
            "definir_preco_de_venda": "definir preco de venda",
            "receber_pagamento": "receber pagamento",
            "entregar_peca": "entregar a peca",
            "concluir_pedido": "concluir pedido",
            "pedido_concluido": "pedido concluido",
            "pedido_cancelado": "pedido cancelado",
        }
        return etapas.get(etapa, etapa)

    def _formatar_numero(self, valor: Any) -> str:
        if valor is None:
            return "0"
        if isinstance(valor, float) and valor.is_integer():
            return str(int(valor))
        return str(valor)

    def _formatar_bytes(self, valor: Any) -> str:
        if valor is None:
            return "0 B"

        try:
            tamanho = float(valor)
        except (TypeError, ValueError):
            return "0 B"

        unidades = ("B", "KB", "MB", "GB")
        indice = 0
        while tamanho >= 1024 and indice < len(unidades) - 1:
            tamanho /= 1024
            indice += 1

        if tamanho.is_integer():
            return f"{int(tamanho)} {unidades[indice]}"

        return f"{tamanho:.1f} {unidades[indice]}"

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
