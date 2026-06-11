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
        if isinstance(resultado, dict) and "itens" in resultado:
            return self._formatar_inventario(resultado.get("itens") or [])

        if isinstance(resultado, dict):
            return self._formatar_resultado_dict(resultado)

        return ["", f"Resultado: {resultado}"]

    def _formatar_resultado_dict(self, resultado: dict[str, Any]) -> list[str]:
        linhas = [""]

        produto = resultado.get("produto")
        quantidade = resultado.get("quantidade")
        quantidade_atual = resultado.get("quantidade_atual")
        movimento_realizado = resultado.get("movimento_realizado")
        motivo = resultado.get("motivo")
        venda_realizada = resultado.get("venda_realizada")

        if produto:
            linhas.append(f"Produto: {produto}")

        atributos = self._formatar_atributos(resultado)
        if atributos:
            linhas.append(f"Variacao: {atributos}")

        if quantidade is not None and quantidade_atual is None:
            linhas.append(f"Saldo: {self._formatar_numero(quantidade)}")

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
        for campo in ("categoria", "cor", "tamanho"):
            valor = dados.get(campo)
            if valor:
                partes.append(str(valor))
        return " / ".join(partes)

    def _formatar_numero(self, valor: Any) -> str:
        if isinstance(valor, float) and valor.is_integer():
            return str(int(valor))
        return str(valor)

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
