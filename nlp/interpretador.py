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

    TERMOS_INVENTARIO = {"inventario"}

    TERMOS_RELATORIOS = {
        "baixo",
        "baixos",
        "historico",
        "hoje",
        "relatorio",
        "relatorios",
    }

    TERMOS_CONTAS = {
        "caixa",
        "contador",
        "contas",
        "deve",
        "devendo",
        "dever",
        "financeiro",
        "lucro",
        "pagou",
        "pago",
        "receber",
        "recebi",
        "recebido",
    }

    TERMOS_COMPRAS = {
        "compra",
        "compras",
        "comprar",
        "compre",
        "comprei",
        "compramos",
        "cotacao",
        "cotar",
        "fornecedor",
        "reposicao",
    }

    TERMOS_PRECIFICACAO = {
        "cobrar",
        "custo",
        "margem",
        "paguei",
        "preco",
        "precificar",
        "reembolso",
        "sugere",
        "sugerir",
        "sugestao",
        "valor",
    }

    TERMOS_PEDIDOS = {
        "cliente",
        "encomenda",
        "encomendado",
        "encomendou",
        "encomendar",
        "pedido",
        "pedidos",
        "pediu",
        "confirmado",
        "confirmei",
        "confirmar",
        "concluido",
        "concluidos",
        "conclui",
        "encerrado",
        "encerrados",
        "entregue",
        "entreguei",
        "entregar",
        "finalizado",
        "finalizados",
        "finalizei",
        "pagamento",
        "pagou",
        "pago",
        "pagos",
        "recebi",
        "recebido",
    }

    TERMOS_QUANTIDADE = {
        "um": "1",
        "uma": "1",
        "dois": "2",
        "duas": "2",
        "tres": "3",
        "quatro": "4",
        "cinco": "5",
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
        "calcinha": "calcinha",
        "calcinhas": "calcinha",
        "cueca": "cueca",
        "cuecas": "cueca",
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

    DETALHES_PRODUTO_MAP = {
        "dupla": "duplo",
        "duplas": "duplo",
        "duplo": "duplo",
        "duplos": "duplo",
        "fio": "fio",
        "fios": "fio",
        "renda": "renda",
        "rendas": "renda",
    }

    PALAVRAS_PRODUTO = (
        set(CATEGORIAS_ROUPA_MAP)
        | set(CORES_MAP)
        | set(DETALHES_PRODUTO_MAP)
        | TAMANHOS
    )

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

        if self._parece_contas(conjunto, entidades):
            return "contas"

        if self._parece_relatorio(conjunto, entidades):
            return "relatorios"

        if self._parece_pedido(conjunto, entidades):
            return "pedidos"

        if self._parece_precificacao(conjunto, entidades):
            return "precificacao"

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

    def _parece_contas(
        self,
        tokens: set[str],
        entidades: dict[str, Any],
    ) -> bool:
        if tokens & {"contador", "contas", "financeiro", "caixa", "lucro"}:
            return True

        if tokens & {"deve", "devendo", "dever"}:
            return True

        if tokens & {"pagou", "pago", "recebi", "recebido"} and entidades.get(
            "valores_monetarios"
        ):
            return True

        if "receber" in tokens and tokens & {"quanto", "tenho", "valor"}:
            return True

        return False

    def _parece_relatorio(
        self,
        tokens: set[str],
        entidades: dict[str, Any],
    ) -> bool:
        if "historico" in tokens:
            return True

        if tokens & {"receber", "lucro"}:
            return True

        if tokens & {"pendente", "pendentes"} and (
            tokens & {"pedido", "pedidos", "compra", "compras"}
        ):
            return True

        if tokens & {
            "concluido",
            "concluidos",
            "encerrado",
            "encerrados",
            "finalizado",
            "finalizados",
            "pago",
            "pagos",
        } and tokens & {"pedido", "pedidos"}:
            return True

        if tokens & {"relatorio", "relatorios"}:
            return True

        if tokens & {"baixo", "baixos"} and (
            tokens & {"estoque", "produto", "produtos"}
            or entidades.get("categorias_roupa")
        ):
            return True

        if "hoje" in tokens and (
            tokens & self.VERBOS_VENDA
            or tokens & {"faturamento", "venda", "vendas"}
        ):
            return True

        return False

    def _parece_precificacao(
        self,
        tokens: set[str],
        entidades: dict[str, Any],
    ) -> bool:
        if not entidades.get("valores_monetarios"):
            return False

        if tokens & self.TERMOS_PRECIFICACAO:
            return True

        if tokens & {"comprei", "compramos"}:
            return True

        return False

    def _parece_pedido(
        self,
        tokens: set[str],
        entidades: dict[str, Any],
    ) -> bool:
        if tokens & self.TERMOS_PEDIDOS:
            return True

        if tokens & self.VERBOS_VENDA and entidades.get("cliente"):
            return True

        if tokens & {
            "concluido",
            "conclui",
            "finalizei",
            "pagou",
            "pago",
            "recebi",
            "recebido",
        } and (entidades.get("cliente") or entidades.get("produto")):
            return True

        if tokens & {"compre", "comprei", "compramos"} and entidades.get("cliente"):
            return True

        if tokens & {"compre", "comprei", "compramos"} and entidades.get("produto"):
            return not (tokens & {"valor", "preco", "custo", "paguei"})

        return False

    def _identificar_intencao(
        self,
        tokens: list[str],
        dominio: str | None,
        entidades: dict[str, Any],
    ) -> str | None:
        if dominio is None:
            return None

        conjunto = set(tokens)

        if dominio == "contas":
            if conjunto & {"pagou", "pago", "recebi", "recebido"}:
                return "contas_registrar_pagamento"

            if conjunto & {"deve", "devendo", "dever"}:
                if entidades.get("valores_monetarios"):
                    return "contas_registrar_divida"
                return "contas_consultar_cliente"

            if "receber" in conjunto:
                return "contas_a_receber"
            if "lucro" in conjunto:
                return "contas_lucro"
            return "contas_resumo"

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

        if dominio == "relatorios":
            if "receber" in conjunto:
                return "relatorios_valor_receber"

            if "lucro" in conjunto:
                return "relatorios_lucro"

            if conjunto & {
                "concluido",
                "concluidos",
                "encerrado",
                "encerrados",
                "finalizado",
                "finalizados",
                "pago",
                "pagos",
            } and conjunto & {"pedido", "pedidos"}:
                return "relatorios_pedidos_concluidos"

            if conjunto & {"pendente", "pendentes"} and conjunto & {"pedido", "pedidos"}:
                return "relatorios_pedidos_pendentes"

            if conjunto & {"pendente", "pendentes"} and conjunto & {"compra", "compras"}:
                return "relatorios_compras_pendentes"

            if "historico" in conjunto:
                return "relatorios_historico_produto"

            if conjunto & {"baixo", "baixos"}:
                return "relatorios_estoque_baixo"

            if "hoje" in conjunto and (
                conjunto & self.VERBOS_VENDA
                or conjunto & {"faturamento", "venda", "vendas"}
            ):
                return "relatorios_vendas_hoje"

            return "relatorios_geral"

        if dominio == "pedidos":
            if (
                conjunto & self.VERBOS_VENDA
                or conjunto
                & {
                    "concluido",
                    "concluidos",
                    "conclui",
                    "encerrado",
                    "encerrados",
                    "finalizei",
                    "finalizado",
                    "finalizados",
                    "pagou",
                    "pago",
                    "pagos",
                    "recebi",
                    "recebido",
                }
            ) and (entidades.get("cliente") or entidades.get("produto")):
                return "pedidos_concluir"

            if conjunto & {"entregue", "entreguei", "entregar"}:
                return "pedidos_entregar"

            if conjunto & {"compre", "comprei", "compramos", "compra"}:
                return "pedidos_registrar_compra"

            if conjunto & {"confirmado", "confirmei", "confirmar"}:
                return "pedidos_confirmar"

            if conjunto & {
                "cliente",
                "encomenda",
                "encomendado",
                "encomendou",
                "encomendar",
                "pedido",
                "pedidos",
                "pediu",
            }:
                return "pedidos_criar"

            return "pedidos_geral"

        if dominio == "precificacao":
            return "precificacao_sugerir_preco"

        if dominio == "compras":
            if conjunto & {"cotacao", "cotar"}:
                return "compras_cotacao"
            if "fornecedor" in conjunto:
                return "compras_fornecedor"
            if "reposicao" in conjunto:
                return "compras_reposicao"
            if conjunto & {
                "compra",
                "compras",
                "comprar",
                "compre",
                "comprei",
                "compramos",
            }:
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
        detalhes = self._extrair_normalizados(tokens, self.DETALHES_PRODUTO_MAP)
        tamanhos = sorted({token for token in tokens if token in self.TAMANHOS})
        valores = self._extrair_valores_monetarios(msg)
        quantidade = self._extrair_quantidade(tokens)

        atributos_roupa = {
            "categoria": categorias,
            "cor": cores,
            "detalhe": detalhes,
            "tamanho": tamanhos,
        }
        produto = self._montar_produto_roupa(atributos_roupa)
        if produto is None:
            produto = self._extrair_produto_generico(msg, tokens)

        return {
            "numeros": re.findall(r"\b\d+(?:[.,]\d+)?\b", msg or ""),
            "valores_monetarios": valores,
            "quantidade": quantidade,
            "cliente": self._extrair_cliente(msg),
            "produto": produto,
            "cores": cores,
            "detalhes_produto": detalhes,
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
                r"\b(?:por|valor(?: de)?|no valor de|preco(?: de)?|custo(?: de)?|paguei|deve|devendo|pagou|pago|recebi|recebido)\s*(?:r\$\s*)?(\d+(?:[.,]\d+)?)",
                self._normalizar(texto),
            )
        )
        return valores

    def _extrair_quantidade(self, tokens: list[str]) -> str | None:
        for indice, token in enumerate(tokens[:-1]):
            proximo = tokens[indice + 1]
            if proximo not in self.CATEGORIAS_ROUPA_MAP:
                continue

            if token in self.TERMOS_QUANTIDADE:
                return self.TERMOS_QUANTIDADE[token]

            if token.replace(",", ".").replace(".", "", 1).isdigit():
                return token

        if any(token in self.CATEGORIAS_ROUPA_MAP for token in tokens):
            return "1"

        return None

    def _extrair_cliente(self, msg: str) -> str | None:
        texto = msg or ""
        encomenda = re.search(
            r"^\s*(\w+)\s+(?:me\s+)?encomendou\b",
            texto,
            flags=re.IGNORECASE,
        )
        if encomenda:
            cliente = encomenda.group(1).strip()
            if self._cliente_valido(cliente):
                return cliente.capitalize()

        padroes = [
            r"^\s*([A-Za-zÀ-ÿ]+)\s+deve\b",
            r"\bquanto\s+([A-Za-zÀ-ÿ]+)\s+deve\b",
            r"\b([A-Za-zÀ-ÿ]+)\s+(?:esta\s+)?devendo\b",
            r"\bcliente\s+([A-Za-zÀ-ÿ]+)",
            r"\bpedido\s+(?:da|do|de)\s+([A-Za-zÀ-ÿ]+)",
            r"\b(?:pra|para)\s+([A-Za-zÀ-ÿ]+)",
            r"\b([A-Za-zÀ-ÿ]+)\s+(?:me\s+)?pagou\b",
            r"\b(?:recebi|recebido)\s+(?:.+?\s)?(?:da|do|de)\s+([A-Za-zÀ-ÿ]+)",
            r"\b(?:camiseta|camisa|calca|calcinha|cueca|bermuda|vestido|blusa|jaqueta|short|saia|tenis)\s+(?:da|do|de)\s+([A-Za-zÀ-ÿ]+)",
        ]

        for padrao in padroes:
            encontrado = re.search(padrao, texto, flags=re.IGNORECASE)
            if not encontrado:
                continue

            cliente = encontrado.group(1).strip()
            if self._cliente_valido(cliente):
                return cliente.capitalize()

        return None

    def _cliente_valido(self, cliente: str) -> bool:
        palavra = self._normalizar(cliente)
        return palavra not in {
            "comprar",
            "continuar",
            "entregar",
            "receber",
            "vender",
        }

    def _montar_produto_roupa(self, atributos: dict[str, list[str]]) -> str | None:
        categoria = self._primeiro(atributos.get("categoria"))
        if not categoria:
            return None

        partes = [
            categoria,
            self._primeiro(atributos.get("cor")),
        ]
        partes.extend(atributos.get("detalhe") or [])
        partes.append(self._primeiro(atributos.get("tamanho")))
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

    def _extrair_produto_generico(
        self,
        msg: str,
        tokens: list[str],
    ) -> str | None:
        produto = self._extrair_produto_por_marcador(msg)
        if produto:
            return produto

        indices_valor = {
            indice
            for indice, token in enumerate(tokens)
            if token in {"valor", "preco", "custo", "paguei", "por"}
        }
        palavras_descartadas = {
            "comprei",
            "compramos",
            "uma",
            "um",
            "umas",
            "uns",
            "no",
            "na",
            "num",
            "numa",
            "de",
            "do",
            "da",
            "por",
            "valor",
            "preco",
            "custo",
            "paguei",
            "qual",
            "quanto",
            "vender",
            "venda",
            "cobrar",
            "reais",
            "real",
        }
        partes = []
        inicio = 0

        if tokens and tokens[0] == "paguei":
            for indice, token in enumerate(tokens):
                if token in {"num", "numa", "em", "no", "na"}:
                    inicio = indice + 1
                    indices_valor = set()
                    break

        for indice, token in enumerate(tokens[inicio:], start=inicio):
            if any(indice >= valor_indice for valor_indice in indices_valor):
                break
            if token in palavras_descartadas:
                continue
            if token in {"valor", "preco", "custo"}:
                break
            if token.replace(",", ".").replace(".", "", 1).isdigit():
                continue
            partes.append(token)

        return " ".join(partes).strip() or None

    def _limpar_produto(self, produto: str) -> str:
        palavras_descartadas = {
            "aqui",
            "com",
            "custo",
            "da",
            "de",
            "do",
            "em",
            "estoque",
            "loja",
            "na",
            "no",
            "por",
            "preco",
            "reais",
            "real",
            "tem",
            "tenho",
            "unidade",
            "unidades",
            "valor",
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
