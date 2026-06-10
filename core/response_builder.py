"""
Construtor de respostas do Cooper.

Este módulo define a classe ResponseBuilder, responsável por transformar os
dicionários internos produzidos pelos agentes em mensagens finais legíveis.

Regra arquitetural principal:
    ResponseBuilder = apresentação

Agentes retornam apenas dados. O Router escolhe o agente. O ResponseBuilder
transforma esses dados em texto compreensível para o usuário ou para a camada
de interface.
"""

from typing import Any


class ResponseBuilder:
    """
    Constrói respostas finais a partir do formato padrão interno do Cooper.

    Esta classe centraliza a apresentação textual para evitar que agentes,
    roteadores ou o núcleo principal espalhem regras de formatação pelo sistema.
    """

    def construir(self, resultado: dict[str, Any]) -> str:
        """
        Constrói uma mensagem final com base no resultado interno recebido.

        Args:
            resultado: Dicionário padronizado produzido por um agente ou pelo
                roteador.

        Returns:
            Texto final pronto para ser exibido ao usuário.
        """
        if not isinstance(resultado, dict):
            return "Não consegui interpretar a resposta interna do Cooper."

        status = resultado.get("status", "indefinido")
        tipo = resultado.get("tipo", "desconhecido")
        erro = resultado.get("erro")
        dados = resultado.get("dados") or {}

        if status == "erro":
            return self._construir_erro(erro=erro)
        
        if status == "nao_processado":
            return self._construir_nao_processado()

        if dados:
            return self._construir_com_dados(
                tipo=tipo,
                dados=dados
            )

        return f"Operação '{tipo}' concluída."

    def _construir_com_dados(self, tipo: str, dados: dict[str, Any]) -> str:
        """
        Constrói uma resposta textual quando há dados estruturados.

        Args:
            tipo: Tipo da resposta.
            dados: Dados estruturados retornados pelo agente.

        Returns:
            Texto formatado contendo a mensagem e os dados relevantes.
        """
        linhas = [f"Operação: {tipo}", ""]

        for chave, valor in dados.items():
            nome_campo = str(chave).replace("_", " ").capitalize()
            linhas.append(f"{nome_campo}: {valor}")

        return "\n".join(linhas).strip()

    def _construir_erro(self, erro: str | None = None) -> str:
        """
        Constrói uma resposta textual para cenários de erro.

        Args:
            erro: Código ou detalhe opcional do erro.

        Returns:
            Texto amigável de erro.
        """
        if erro:
            return f"Erro: {erro}"
        return "Ocorreu um erro durante o processamento."
    
    def _construir_nao_processado(self) -> str:
        """
        Constrói uma resposta textual quando nenhum agente atende à mensagem.

        Returns:
            Texto amigável informando que a solicitação não foi entendida.
        """
        return (
            "Ainda não sei qual área deve cuidar dessa solicitação. "
            "Por favor, reformule sua pergunta."
        )

    def construir_debug(self, resultado: dict[str, Any]) -> str:
        """
        Constrói uma resposta detalhada para depuração interna.

        Args:
            resultado: Dicionário padronizado produzido pelo Cooper.

        Returns:
            Texto com campos internos relevantes para análise técnica.
        """
        if not isinstance(resultado, dict):
            return "Resultado inválido para depuração."

        return (
            f"Agente: {resultado.get('agente')}\n"
            f"Status: {resultado.get('status')}\n"
            f"Tipo: {resultado.get('tipo')}\n"
            f"Dados: {resultado.get('dados')}\n"
            f"Erro: {resultado.get('erro')}"
        )
