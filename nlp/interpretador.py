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
            "cotar",
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
            "camiseta",
            "camisa",
            "calca",
            "bermuda",
            "vestido",
            "blusa",
            "jaqueta",
            "short",
            "saia",
            "tenis",
        },
    }

    CORES = {
        "amarelo",
        "amarela",
        "azul",
        "bege",
        "branco",
        "branca",
        "cinza",
        "laranja",
        "marrom",
        "preto",
        "preta",
        "rosa",
        "roxo",
        "roxa",
        "verde",
        "vermelho",
        "vermelha",
    }

    TAMANHOS = {
        "pp",
        "p",
        "m",
        "g",
        "gg",
        "xg",
        "xgg",
        "36",
        "38",
        "40",
        "42",
        "44",
        "46",
        "48",
        "50",
    }

    CATEGORIAS_ROUPA = {
        "bermuda",
        "blusa",
        "calca",
        "camisa",
        "camiseta",
        "jaqueta",
        "saia",
        "short",
        "tenis",
        "vestido",
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
        tokens = set(texto.split())

        if tokens & {"vendi", "vender", "vende", "vendemos", "venda"}:
            return "vendas"

        if tokens & {"entrada", "saida", "saldo", "inventario"}:
            return "estoque"

        if tokens & {"compra", "compras", "comprar", "comprei", "cotacao", "cotar"}:
            return "compras"

        pontuacoes: dict[str, int] = {}

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

            if "orcamento" in tokens:
                return "vendas_orcamento"

            if "pedido" in tokens:
                return "vendas_pedido"

            if "cliente" in tokens:
                return "vendas_cliente"

            if "faturamento" in tokens:
                return "vendas_faturamento"

            if tokens & {
                "vender",
                "vende",
                "vendi",
                "vendemos",
                "venda",
            }:
                return "vendas_registrar"

            return "vendas_geral"

        if dominio == "compras":

            tokens = set(texto.split())

            if tokens & {"cotacao", "cotar"}:
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
        texto_normalizado = self._normalizar(msg)
        tokens = set(texto_normalizado.split())
        categorias = sorted(tokens & self.CATEGORIAS_ROUPA)
        cores = sorted(tokens & self.CORES)
        tamanhos = sorted(tokens & self.TAMANHOS)

        return {
            "numeros": numeros,
            "valores_monetarios": valores,
            "produto": self._extrair_produto(msg),
            "cores": cores,
            "tamanhos": tamanhos,
            "categorias_roupa": categorias,
            "atributos_roupa": {
                "categoria": categorias,
                "cor": cores,
                "tamanho": tamanhos,
            },
        }

    def _extrair_produto(self, msg: str) -> str | None:
        texto = " ".join((msg or "").strip().split())
        texto_lower = self._normalizar(texto)

        marcadores = [
            "produto ",
            "produtos ",
            "entrada de ",
            "saida de ",
            "vendi ",
            "vender ",
            "venda de ",
            "saldo de ",
            "saldo do ",
            "saldo da ",
        ]

        for marcador in marcadores:
            indice = texto_lower.find(marcador)
            if indice >= 0:
                inicio = indice + len(marcador)
                produto = texto[inicio:].strip()
                produto = self._limpar_produto(produto)
                return produto or None

        return None

    def _limpar_produto(self, produto: str) -> str:
        palavras_descartadas = {
            "por",
            "com",
            "de",
            "do",
            "da",
            "no",
            "na",
            "unidade",
            "unidades",
        }
        partes = []

        for parte in produto.split():
            if parte.lower().startswith("r$"):
                break
            if parte.replace(",", ".").replace(".", "", 1).isdigit():
                continue
            if parte.lower() in palavras_descartadas:
                continue
            partes.append(parte.strip(".,;:"))

        return " ".join(partes).strip()
