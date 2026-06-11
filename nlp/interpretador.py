"""
Interpretador NLP do Cooper.

Responsabilidade desta camada:
    - normalizar texto
    - sugerir dominio
    - sugerir intencao
    - extrair entidades

Ela nao escolhe agente, nao executa regra de negocio e nao formata resposta.
"""

import re
import unicodedata
from typing import Any


class Interpretador:
    """Interpreta mensagens recebidas pelo Cooper."""

    VERBOS_VENDA = {
        "venda",
        "vende",
        "vender",
        "vendi",
        "vendemos",
        "vendeu",
        "vendido",
    }

    VERBOS_ENTRADA_ESTOQUE = {
        "adiciona",
        "adicione",
        "chegou",
        "chegaram",
        "coloca",
        "coloque",
        "coloquei",
        "entrada",
        "entrou",
        "recebi",
        "recebemos",
    }

    VERBOS_SAIDA_ESTOQUE = {
        "baixa",
        "baixar",
        "retira",
        "retire",
        "retirei",
        "saida",
        "saiu",
        "tira",
        "tirar",
        "tirei",
    }

    TERMOS_CONSULTA_ESTOQUE = {
        "consultar",
        "consulta",
        "estoque",
        "quantas",
        "quantidade",
        "quanto",
        "saldo",
        "tem",
        "tenho",
    }

    TERMOS_INVENTARIO = {"inventario", "relatorio"}

    TERMOS_COMPRAS = {
        "compra",
        "compras",
        "comprar",
        "comprei",
        "compramos",
        "cotacao",
        "cotar",
        "fornecedor",
        "reposicao",
    }

    CORES_MAP = {
        "amarela": "amarela",
        "amarelas": "amarela",
        "amarelo": "amarela",
        "amarelos": "amarela",
        "azul": "azul",
        "azuis": "azul",
        "bege": "bege",
        "beiges": "bege",
        "branca": "branca",
        "brancas": "branca",
        "branco": "branca",
        "brancos": "branca",
        "cinza": "cinza",
        "cinzas": "cinza",
        "laranja": "laranja",
        "laranjas": "laranja",
        "marrom": "marrom",
        "marrons": "marrom",
        "preta": "preta",
        "pretas": "preta",
        "preto": "preta",
        "pretos": "preta",
        "rosa": "rosa",
        "rosas": "rosa",
        "roxa": "roxa",
        "roxas": "roxa",
        "roxo": "roxa",
        "roxos": "roxa",
        "verde": "verde",
        "verdes": "verde",
        "vermelha": "vermelha",
        "vermelhas": "vermelha",
        "vermelho": "vermelha",
        "vermelhos": "vermelha",
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

    CATEGORIAS_ROUPA_MAP = {
        "bermuda": "bermuda",
        "bermudas": "bermuda",
        "blusa": "blusa",
        "blusas": "blusa",
        "calca": "calca",
        "calcas": "calca",
        "camisa": "camisa",
        "camisas": "camisa",
        "camiseta": "camiseta",
        "camisetas": "camiseta",
        "jaqueta": "jaqueta",
        "jaquetas": "jaqueta",
        "saia": "saia",
        "saias": "saia",
        "short": "short",
        "shorts": "short",
        "tenis": "tenis",
        "vestido": "vestido",
        "vestidos": "vestido",
    }

    PALAVRAS_PRODUTO = set(CATEGORIAS_ROUPA_MAP) | set(CORES_MAP) | TAMANHOS

    def interpretar(self, msg: str) -> dict[str, Any]:
        """Interpreta uma mensagem e retorna uma analise estruturada."""
        texto_original = msg or ""
        texto_normalizado = self._normalizar(texto_original)
        tokens = self._tokenizar(texto_normalizado)
        entidades = self._extrair_entidades(texto_original)
        dominio = self._identificar_dominio(tokens, entidades)
        intencao = self._identificar_intencao(tokens, dominio, entidades)

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
        texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
        return texto

    def _tokenizar(self, texto: str) -> list[str]:
        return [
            token.strip(".,;:?!()[]{}")
            for token in texto.split()
            if token.strip(".,;:?!()[]{}")
        ]

    def _identificar_dominio(
        self,
        tokens: list[str],
        entidades: dict[str, Any],
    ) -> str | None:
        conjunto = set(tokens)

        if conjunto & self.VERBOS_VENDA:
            return "vendas"

        if conjunto & self.TERMOS_COMPRAS:
            return "compras"

        if conjunto & (
            self.VERBOS_ENTRADA_ESTOQUE
            | self.VERBOS_SAIDA_ESTOQUE
            | self.TERMOS_INVENTARIO
        ):
            return "estoque"

        if conjunto & self.TERMOS_CONSULTA_ESTOQUE and entidades.get("produto"):
            return "estoque"

        if entidades.get("categorias_roupa"):
            return "estoque"

        return None

    def _identificar_intencao(
        self,
        tokens: list[str],
        dominio: str | None,
        entidades: dict[str, Any],
    ) -> str | None:
        if dominio is None:
            return None

        conjunto = set(tokens)

        if dominio == "vendas":
            if "orcamento" in conjunto:
                return "vendas_orcamento"
            if "pedido" in conjunto:
                return "vendas_pedido"
            if "cliente" in conjunto:
                return "vendas_cliente"
            if "faturamento" in conjunto:
                return "vendas_faturamento"
            if conjunto & self.VERBOS_VENDA:
                return "vendas_registrar"
            return "vendas_geral"

        if dominio == "compras":
            if conjunto & {"cotacao", "cotar"}:
                return "compras_cotacao"
            if "fornecedor" in conjunto:
                return "compras_fornecedor"
            if "reposicao" in conjunto:
                return "compras_reposicao"
            if conjunto & {"compra", "compras", "comprar", "comprei", "compramos"}:
                return "compras_registrar"
            return "compras_geral"

        if dominio == "estoque":
            if conjunto & self.TERMOS_INVENTARIO:
                return "estoque_inventario"
            if conjunto & self.VERBOS_ENTRADA_ESTOQUE:
                return "estoque_entrada"
            if conjunto & self.VERBOS_SAIDA_ESTOQUE:
                return "estoque_saida"
            if conjunto & self.TERMOS_CONSULTA_ESTOQUE and entidades.get("produto"):
                return "estoque_consulta_saldo"
            return "estoque_geral"

        return None

    def _extrair_entidades(self, msg: str) -> dict[str, Any]:
        texto_normalizado = self._normalizar(msg)
        tokens = self._tokenizar(texto_normalizado)
        categorias = self._extrair_normalizados(tokens, self.CATEGORIAS_ROUPA_MAP)
        cores = self._extrair_normalizados(tokens, self.CORES_MAP)
        tamanhos = sorted({token for token in tokens if token in self.TAMANHOS})
        valores = self._extrair_valores_monetarios(msg)

        atributos_roupa = {
            "categoria": categorias,
            "cor": cores,
            "tamanho": tamanhos,
        }
        produto = self._montar_produto_roupa(atributos_roupa)
        if produto is None:
            produto = self._extrair_produto_por_marcador(msg)

        return {
            "numeros": re.findall(r"\b\d+(?:[.,]\d+)?\b", msg or ""),
            "valores_monetarios": valores,
            "produto": produto,
            "cores": cores,
            "tamanhos": tamanhos,
            "categorias_roupa": categorias,
            "atributos_roupa": atributos_roupa,
        }

    def _extrair_normalizados(
        self,
        tokens: list[str],
        mapa: dict[str, str],
    ) -> list[str]:
        encontrados = []
        for token in tokens:
            valor = mapa.get(token)
            if valor and valor not in encontrados:
                encontrados.append(valor)
        return encontrados

    def _extrair_valores_monetarios(self, msg: str) -> list[str]:
        texto = msg or ""
        valores = re.findall(r"R\$\s*\d+(?:[.,]\d+)?", texto, flags=re.IGNORECASE)
        valores.extend(
            re.findall(
                r"\b(?:por|valor|preco|preco de)\s*(?:r\$\s*)?(\d+(?:[.,]\d+)?)",
                self._normalizar(texto),
            )
        )
        return valores

    def _montar_produto_roupa(self, atributos: dict[str, list[str]]) -> str | None:
        categoria = self._primeiro(atributos.get("categoria"))
        if not categoria:
            return None

        partes = [
            categoria,
            self._primeiro(atributos.get("cor")),
            self._primeiro(atributos.get("tamanho")),
        ]
        return " ".join(parte for parte in partes if parte)

    def _extrair_produto_por_marcador(self, msg: str) -> str | None:
        texto = " ".join((msg or "").strip().split())
        texto_lower = self._normalizar(texto)

        marcadores = [
            "produto ",
            "produtos ",
            "entrada de ",
            "saida de ",
            "chegou ",
            "chegaram ",
            "recebi ",
            "recebemos ",
            "coloquei ",
            "vendi ",
            "vendemos ",
            "vender ",
            "venda de ",
            "saldo de ",
            "saldo do ",
            "saldo da ",
            "quantas ",
            "quantos ",
            "quanto ",
            "tem ",
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
            "aqui",
            "com",
            "da",
            "de",
            "do",
            "em",
            "estoque",
            "loja",
            "na",
            "no",
            "por",
            "reais",
            "real",
            "tem",
            "tenho",
            "unidade",
            "unidades",
        }
        partes = []

        for parte in produto.split():
            palavra = self._normalizar(parte.strip(".,;:?!"))
            if not palavra:
                continue
            if palavra.startswith("r$"):
                break
            if palavra.replace(",", ".").replace(".", "", 1).isdigit():
                continue
            if palavra in palavras_descartadas:
                continue
            partes.append(palavra)

        return " ".join(partes).strip()

    def _primeiro(self, valores: list[str] | None) -> str | None:
        if valores:
            return valores[0]
        return None
