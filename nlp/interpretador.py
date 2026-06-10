"""
Interpretador NLP do Cooper.

Este módulo define o Interpretador, responsável por realizar uma análise inicial
da mensagem antes que ela seja encaminhada ao Router. A implementação é simples,
previsível e baseada em regras, servindo como base estável para evoluções
futuras.

Regra arquitetural principal:
    Interpretador = análise sem decisão final

O interpretador pode sugerir domínio e intenção, mas não escolhe o agente final
e não formata a resposta ao usuário.
"""

import re
import unicodedata
from typing import Any


class Interpretador:
    """
    Interpreta mensagens recebidas pelo Cooper.

    Esta classe aplica regras leves de normalização e identificação inicial de
    domínio, intenção e entidades. O objetivo é enriquecer o processamento sem
    substituir a responsabilidade do Router ou dos agentes especializados.
    """

    DOMINIOS = {
        "vendas": {
            "venda",
            "vendas",
            "vende",
            "vendi",
            "vender",
            "pedido",
            "cliente",
            "orcamento",
            "faturamento",
        },
            "compras": {
            "compra",
            "compras",
            "comprar",
            "comprei",
            "compramos",
            "fornecedor",
            "cotacao",
            "reposicao",
        },
        "estoque": {
            "estoque",
            "produto",
            "produtos",
            "saldo",
            "inventario",
            "entrada",
            "saida",
        },
    }

    def interpretar(self, msg: str) -> dict[str, Any]:
        """
        Interpreta uma mensagem e retorna uma análise estruturada.

        Args:
            msg: Mensagem original enviada ao Cooper.

        Returns:
            Dicionário contendo texto normalizado, domínio sugerido, intenção
            sugerida e entidades básicas extraídas.
        """
        texto_original = msg or ""
        texto_normalizado = self._normalizar(texto_original)
        dominio = self._identificar_dominio(texto_normalizado)
        intencao = self._identificar_intencao(texto_normalizado, dominio)
        entidades = self._extrair_entidades(texto_original)

        return {
            "texto_original": texto_original,
            "texto_normalizado": texto_normalizado,
            "dominio": dominio,
            "intencao": intencao,
            "entidades": entidades,
        }


    def _normalizar(self, msg: str) -> str:
        texto = " ".join((msg or "").lower().strip().split())

        texto = unicodedata.normalize("NFD", texto)
        texto = "".join(
            c for c in texto
            if unicodedata.category(c) != "Mn"
        )

        return texto

    def _identificar_dominio(self, texto: str) -> str | None:
        """
        Sugere o domínio mais provável da mensagem.

        Args:
            texto: Texto já normalizado.

        Returns:
            Nome do domínio identificado ou None quando não houver evidência.
        """
        pontuacoes: dict[str, int] = {}

        tokens = set(texto.split())

        for dominio, palavras in self.DOMINIOS.items():
            pontuacoes[dominio] = len(tokens & palavras)

        melhor_dominio = max(pontuacoes, key=pontuacoes.get)

        if pontuacoes[melhor_dominio] == 0:
            return None

        return melhor_dominio

    def _identificar_intencao(self, texto: str, dominio: str | None) -> str | None:
        """
        Sugere uma intenção inicial com base no texto e no domínio.

        Args:
            texto: Texto normalizado.
            dominio: Domínio sugerido previamente.

        Returns:
            Nome da intenção sugerida ou None quando não houver evidência.
        """
        if dominio is None:
            return None

        if dominio == "vendas":

            tokens = set(texto.split())

            if tokens & {
                "vender",
                "vende",
                "vendi",
                "vendemos",
                "venda",
            }:
                return "vendas_registrar"

            if "orcamento" in tokens:
                return "vendas_orcamento"

            if "pedido" in tokens:
                return "vendas_pedido"

            if "cliente" in tokens:
                return "vendas_cliente"

            if "faturamento" in tokens:
                return "vendas_faturamento"

            return "vendas_geral"

        if dominio == "compras":

            tokens = set(texto.split())

            if "cotacao" in tokens:
                return "compras_cotacao"

            if "fornecedor" in tokens:
                return "compras_fornecedor"

            if "reposicao" in tokens:
                return "compras_reposicao"

            if tokens & {
                "compra",
                "compras",
                "comprar",
                "comprei",
                "compramos",
            }:
                return "compras_registrar"

            return "compras_geral"
    
        if dominio == "estoque":
            if "saldo" in texto or "quantidade" in texto:
                return "estoque_consulta_saldo"
            if "entrada" in texto:
                return "estoque_entrada"
            if "saida" in texto:
                return "estoque_saida"
            if "inventario" in texto:
                return "estoque_inventario"
            return "estoque_geral"
        return None

    def _extrair_entidades(self, msg: str) -> dict[str, Any]:
        """
        Extrai entidades simples da mensagem.
        Args:
            msg: Mensagem original.
        Returns:
            Dicionário com números e valores monetários encontrados.
        """
        numeros = re.findall(r"\b\d+(?:[.,]\d+)?\b", msg or "")
        valores = re.findall(r"R\$\s*\d+(?:[.,]\d+)?", msg or "", flags=re.IGNORECASE)
        return {
            "numeros": numeros,
            "valores_monetarios": valores,
        }
