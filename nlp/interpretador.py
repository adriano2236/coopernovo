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
        "dia",
        "fechamento",
        "fechar",
        "historico",
        "hoje",
        "relatorio",
        "relatorios",
        "resumo",
    }

    TERMOS_BUSCA = {
        "achar",
        "ache",
        "busca",
        "buscar",
        "encontra",
        "encontrar",
        "encontre",
        "localiza",
        "localizar",
        "localize",
        "pesquisa",
        "pesquisar",
        "procura",
        "procurar",
        "procure",
    }

    TERMOS_BACKUP = {
        "backup",
        "backups",
        "banco",
        "bkp",
        "copia",
        "copiar",
        "copie",
        "csv",
        "dados",
        "excel",
        "exportacao",
        "exportacoes",
        "exportar",
        "exporte",
        "json",
        "planilha",
        "salva",
        "salvar",
        "salve",
        "sqlite",
    }

    TERMOS_AGENDA = {
        "agenda",
        "afazeres",
        "acao",
        "acoes",
        "fazer",
        "hoje",
        "loja",
        "pendencia",
        "pendencias",
        "preciso",
        "prioridade",
        "prioridades",
        "tarefas",
        "trabalho",
    }

    TERMOS_MEMORIA = {
        "apague",
        "apagar",
        "apelido",
        "apelidos",
        "aprendido",
        "aprendidos",
        "aprendizado",
        "aprendizados",
        "conversa",
        "contexto",
        "esqueca",
        "esquecer",
        "estrategia",
        "estrategica",
        "estrategicas",
        "estrategico",
        "estrategicos",
        "fase",
        "guarde",
        "guardar",
        "imediato",
        "lembra",
        "lembrar",
        "lembre",
        "meta",
        "metas",
        "memoria",
        "memorias",
        "memoriza",
        "memorizar",
        "memorize",
        "operacional",
        "operacionais",
        "padrao",
        "padroes",
        "preferencia",
        "preferencias",
        "prefiro",
        "previsao",
        "previsoes",
        "regra",
        "regras",
        "sugestao",
        "sugestoes",
        "tendencia",
        "tendencias",
    }

    TERMOS_CLIENTES = {
        "anota",
        "anotar",
        "anote",
        "cadastro",
        "cadastrar",
        "cadastre",
        "celular",
        "cliente",
        "clientes",
        "contato",
        "contatos",
        "dados",
        "endereco",
        "enderecos",
        "lista",
        "listar",
        "mostra",
        "mostrar",
        "obs",
        "observacao",
        "observacoes",
        "gosta",
        "mora",
        "paga",
        "prefere",
        "telefone",
        "telefones",
        "usa",
        "veste",
        "whatsapp",
        "zap",
    }

    TERMOS_FORNECEDORES = {
        "anota",
        "anotar",
        "anote",
        "atacado",
        "cadastro",
        "cadastrar",
        "cadastre",
        "celular",
        "compra",
        "comprar",
        "contato",
        "contatos",
        "dados",
        "endereco",
        "enderecos",
        "fornecedor",
        "fornecedora",
        "fornecedores",
        "fornece",
        "fornecem",
        "lista",
        "listar",
        "loja",
        "mostra",
        "mostrar",
        "obs",
        "observacao",
        "observacoes",
        "produto",
        "produtos",
        "telefone",
        "telefones",
        "vende",
        "vendem",
        "whatsapp",
        "zap",
    }

    TERMOS_CONTAS = {
        "caixa",
        "coloquei",
        "contador",
        "contas",
        "deve",
        "devendo",
        "dever",
        "despesa",
        "despesas",
        "entrou",
        "entrada",
        "financeiro",
        "gastei",
        "gasto",
        "gastos",
        "lucro",
        "pagamento",
        "paguei",
        "pagou",
        "pago",
        "receber",
        "recebi",
        "recebido",
        "retirei",
        "saiu",
        "saida",
        "tirei",
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
        "altera",
        "alterar",
        "alterei",
        "cancela",
        "cancelado",
        "cancelar",
        "cancelei",
        "achar",
        "achei",
        "encomenda",
        "encomendado",
        "encomendou",
        "encomendar",
        "encontrar",
        "encontrei",
        "corrige",
        "corrigir",
        "desistiu",
        "edita",
        "editar",
        "pedido",
        "pedidos",
        "pediu",
        "confirmado",
        "confirmei",
        "confirmar",
        "concluir",
        "concluido",
        "concluidos",
        "conclui",
        "encerra",
        "encerrar",
        "encerrado",
        "encerrados",
        "entregue",
        "entreguei",
        "entregar",
        "finaliza",
        "finalizar",
        "finalizado",
        "finalizados",
        "finalizei",
        "historico",
        "linha",
        "pagamento",
        "pagou",
        "pago",
        "pagos",
        "procura",
        "procurar",
        "procurando",
        "procure",
        "recebi",
        "recebido",
        "troca",
        "trocar",
        "tempo",
        "ver",
        "veja",
        "muda",
        "mudar",
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
        "moletom": "moletom",
        "moleton": "moletom",
        "moletons": "moletom",
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
        "bonita": "bonito",
        "bonitas": "bonito",
        "bonito": "bonito",
        "bonitos": "bonito",
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

        if self._parece_memoria(conjunto):
            return "memoria"

        if self._parece_backup(conjunto):
            return "backup"

        if self._parece_agenda(conjunto):
            return "agenda"

        if self._parece_busca(conjunto, entidades):
            return "busca"

        if self._parece_fornecedor(conjunto, entidades):
            return "fornecedores"

        if self._parece_cliente(conjunto, entidades):
            return "clientes"

        if self._parece_relatorio(conjunto, entidades):
            return "relatorios"

        if self._parece_pedido(conjunto, entidades):
            return "pedidos"

        if self._parece_contas(conjunto, entidades):
            return "contas"

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

    def _parece_backup(self, tokens: set[str]) -> bool:
        if tokens & {
            "backup",
            "backups",
            "bkp",
            "exportacao",
            "exportacoes",
            "exportar",
            "exporte",
        }:
            return True

        if tokens & {"csv", "excel", "json", "planilha"} and tokens & {
            "dados",
            "banco",
            "cooper",
        }:
            return True

        if tokens & {"copia", "copiar", "copie", "salva", "salvar", "salve"}:
            return bool(tokens & {"banco", "dados", "sqlite", "cooper"})

        return False

    def _parece_agenda(self, tokens: set[str]) -> bool:
        if tokens & {"agenda", "afazeres", "prioridade", "prioridades", "tarefas"}:
            return True

        if tokens & {"pendencia", "pendencias"}:
            return True

        if tokens & {"preciso", "fazer"} and tokens & {
            "cobrar",
            "comprar",
            "entregar",
            "hoje",
            "loja",
            "pedido",
            "pedidos",
        }:
            return True

        return False

    def _parece_busca(
        self,
        tokens: set[str],
        entidades: dict[str, Any],
    ) -> bool:
        if not tokens & self.TERMOS_BUSCA:
            return False

        if tokens & {"historico", "linha"} and tokens & {"pedido", "pedidos"}:
            return False

        if tokens & {"achar", "ache", "procura", "procurar", "procure"}:
            if entidades.get("cliente") and entidades.get("produto"):
                return False

        return True

    def _parece_memoria(self, tokens: set[str]) -> bool:
        if tokens & {"sugestao", "sugestoes"} and tokens & {
            "cobrar",
            "custo",
            "margem",
            "preco",
            "precificar",
            "reembolso",
            "valor",
        }:
            return False

        if tokens & self.TERMOS_MEMORIA:
            return True

        if "historico" in tokens and "conversa" in tokens:
            return True

        return False

    def _parece_fornecedor(
        self,
        tokens: set[str],
        entidades: dict[str, Any],
    ) -> bool:
        if tokens & {"pediu", "pedido", "pedidos", "encomendou", "encomenda"}:
            return False

        if tokens & {
            "fornecedor",
            "fornecedora",
            "fornecedores",
            "atacado",
        }:
            return True

        if entidades.get("fornecedor"):
            return True

        if tokens & {"onde", "quem"} and tokens & {
            "compra",
            "comprar",
            "fornece",
            "fornecem",
            "vende",
            "vendem",
        }:
            return bool(entidades.get("produto"))

        if tokens & {"fornece", "fornecem", "vende", "vendem"}:
            return bool(entidades.get("fornecedor"))

        if entidades.get("endereco_fornecedor") or entidades.get(
            "observacao_fornecedor"
        ):
            return bool(entidades.get("fornecedor"))

        return False

    def _parece_cliente(
        self,
        tokens: set[str],
        entidades: dict[str, Any],
    ) -> bool:
        if tokens & {"pediu", "pedido", "pedidos", "encomendou", "encomenda"}:
            return False

        if tokens & {
            "cadastro",
            "cadastrar",
            "cadastre",
            "clientes",
            "contato",
            "contatos",
            "dados",
            "endereco",
            "enderecos",
            "telefone",
            "telefones",
            "whatsapp",
            "zap",
        }:
            return True

        if tokens & {"anota", "anotar", "anote", "obs", "observacao", "observacoes"}:
            return bool(entidades.get("cliente"))

        if tokens & {"gosta", "prefere", "paga", "usa", "mora", "veste"}:
            return bool(entidades.get("cliente"))

        if entidades.get("telefone") or entidades.get("endereco"):
            return bool(entidades.get("cliente"))

        return False

    def _parece_contas(
        self,
        tokens: set[str],
        entidades: dict[str, Any],
    ) -> bool:
        if tokens & {"paguei"} and tokens & {
            "cobrar",
            "preco",
            "precificar",
            "sugere",
            "sugerir",
            "vender",
        }:
            return False

        if tokens & {"contador", "contas", "financeiro", "caixa", "lucro"}:
            return True

        if tokens & {"despesa", "despesas", "gasto", "gastos"}:
            return True

        if tokens & {"gastei", "paguei"}:
            return bool(entidades.get("valores_monetarios"))

        if tokens & {
            "coloquei",
            "entrou",
            "entrada",
            "retirei",
            "saiu",
            "saida",
            "tirei",
        } and "caixa" in tokens:
            return True

        if "pagamento" in tokens and entidades.get("valores_monetarios"):
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
        if tokens & {"fechamento", "fechar"}:
            return True

        if tokens & {"resumo"} and tokens & {"dia", "hoje", "loja"}:
            return True

        if "hoje" in tokens and tokens & {"como", "foi"}:
            return True

        if "historico" in tokens and tokens & {"pedido", "pedidos"}:
            return False

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
        if entidades.get("pedido_id") and tokens & {
            "cancela",
            "cancelar",
            "cancelei",
            "compre",
            "comprei",
            "compramos",
            "compra",
            "confirmei",
            "confirmar",
            "concluir",
            "conclui",
            "encerra",
            "encerrar",
            "entregue",
            "entreguei",
            "entregar",
            "finaliza",
            "finalizar",
            "finalizei",
            "achei",
            "encontrei",
            "pedido",
            "pago",
        }:
            return True

        if tokens & {"pagamento", "pagou", "pago", "recebi", "recebido"} and entidades.get(
            "valores_monetarios"
        ):
            return False

        if tokens & self.TERMOS_PEDIDOS:
            return True

        if tokens & {
            "achar",
            "achei",
            "encontrar",
            "encontrei",
            "procura",
            "procurar",
            "procurando",
            "procure",
            "ver",
            "veja",
        } and entidades.get("cliente") and entidades.get("produto"):
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

        if dominio == "backup":
            if conjunto & {"lista", "listar", "mostra", "mostrar", "ver", "veja"}:
                return "backup_listar"

            if conjunto & {
                "csv",
                "excel",
                "exportacao",
                "exportacoes",
                "exportar",
                "exporte",
                "json",
                "planilha",
            }:
                return "backup_exportar"

            return "backup_criar"

        if dominio == "agenda":
            return "agenda_hoje"

        if dominio == "busca":
            return "busca_geral"

        if dominio == "memoria":
            if conjunto & {
                "guarde",
                "guardar",
                "lembre",
                "memoriza",
                "memorizar",
                "memorize",
            }:
                return "memoria_guardar"

            if entidades.get("memoria_texto"):
                return "memoria_guardar"

            if conjunto & {"apague", "apagar", "esqueca", "esquecer"}:
                return "memoria_esquecer"

            if "historico" in conjunto and "conversa" in conjunto:
                return "memoria_historico"

            return "memoria_listar"

        if dominio == "fornecedores":
            if conjunto & {"lista", "listar", "mostra", "mostrar"} and conjunto & {
                "fornecedor",
                "fornecedora",
                "fornecedores",
            }:
                return "fornecedores_listar"

            if conjunto & {
                "anota",
                "anotar",
                "anote",
                "obs",
                "observacao",
                "observacoes",
            }:
                return "fornecedores_anotar"

            if entidades.get("produto") and (
                conjunto & {"fornece", "fornecem", "produto", "produtos", "vende", "vendem"}
            ) and entidades.get("fornecedor"):
                return "fornecedores_vincular_produto"

            if entidades.get("produto") and (
                conjunto & {"fornecedor", "fornecedora", "fornecedores", "onde", "quem"}
            ) and not entidades.get("fornecedor"):
                return "fornecedores_buscar_produto"

            if conjunto & {"cadastro", "cadastrar", "cadastre"}:
                return "fornecedores_criar"

            if entidades.get("telefone") or entidades.get("endereco_fornecedor"):
                return "fornecedores_atualizar"

            if conjunto & {
                "fornecedor",
                "fornecedora",
                "fornecedores",
            } and not entidades.get("fornecedor"):
                return "fornecedores_listar"

            return "fornecedores_consultar"

        if dominio == "clientes":
            if conjunto & {"lista", "listar", "mostra", "mostrar"} and conjunto & {
                "clientes",
                "contatos",
            }:
                return "clientes_listar"

            if conjunto & {
                "anota",
                "anotar",
                "anote",
                "gosta",
                "mora",
                "obs",
                "observacao",
                "observacoes",
                "paga",
                "prefere",
                "usa",
                "veste",
            }:
                return "clientes_anotar"

            if conjunto & {"cadastro", "cadastrar", "cadastre"}:
                return "clientes_criar"

            if entidades.get("telefone") or entidades.get("endereco"):
                return "clientes_atualizar"

            if conjunto & {"clientes", "contatos"} and not entidades.get("cliente"):
                return "clientes_listar"

            return "clientes_consultar"

        if dominio == "contas":
            if "caixa" in conjunto and conjunto & {
                "entrou",
                "entrada",
                "coloquei",
                "recebi",
            }:
                return "contas_caixa_entrada"

            if "caixa" in conjunto and conjunto & {
                "retirei",
                "saiu",
                "saida",
                "tirei",
            }:
                return "contas_caixa_saida"

            if "caixa" in conjunto:
                return "contas_caixa_resumo"

            if conjunto & {"despesa", "despesas", "gasto", "gastos"}:
                if entidades.get("valores_monetarios"):
                    return "contas_registrar_despesa"
                return "contas_despesas_listar"

            if conjunto & {"gastei", "paguei"}:
                return "contas_registrar_despesa"

            if conjunto & {"pagamento", "pagou", "pago", "recebi", "recebido"}:
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
            if (
                conjunto & {"fechamento", "fechar"}
                or (conjunto & {"resumo"} and conjunto & {"dia", "hoje", "loja"})
                or ("hoje" in conjunto and conjunto & {"como", "foi"})
            ):
                return "relatorios_fechamento_dia"

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
            if "historico" in conjunto or (
                "linha" in conjunto and "tempo" in conjunto
            ):
                return "pedidos_historico"

            if conjunto & {"nao", "ainda"} and conjunto & {
                "achei",
                "encontrei",
            }:
                return "pedidos_nao_encontrado"

            if conjunto & {"achei", "encontrei"}:
                return "pedidos_encontrado"

            if conjunto & {
                "achar",
                "procura",
                "procurar",
                "procurando",
                "procure",
                "ver",
                "veja",
            }:
                return "pedidos_procurar"

            if conjunto & {
                "cancela",
                "cancelado",
                "cancelar",
                "cancelei",
                "desistiu",
            }:
                return "pedidos_cancelar"

            if conjunto & {
                "altera",
                "alterar",
                "alterei",
                "corrige",
                "corrigir",
                "edita",
                "editar",
                "muda",
                "mudar",
                "troca",
                "trocar",
            }:
                return "pedidos_editar"

            if conjunto & {"pagamento", "pagou", "pago", "pagos", "recebi", "recebido"}:
                return "pedidos_registrar_pagamento"

            if conjunto & {"entregue", "entreguei", "entregar"}:
                return "pedidos_entregar"

            if (
                conjunto & self.VERBOS_VENDA
                or conjunto
                & {
                    "concluido",
                    "concluidos",
                    "concluir",
                    "conclui",
                    "encerra",
                    "encerrar",
                    "encerrado",
                    "encerrados",
                    "finaliza",
                    "finalizar",
                    "finalizei",
                    "finalizado",
                    "finalizados",
                }
            ) and (
                entidades.get("pedido_id")
                or entidades.get("cliente")
                or entidades.get("produto")
            ):
                return "pedidos_concluir"

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
        tamanhos = self._extrair_tamanhos(tokens)
        valores = self._extrair_valores_monetarios(msg)
        quantidade = self._extrair_quantidade(tokens)
        pedido_id = self._extrair_pedido_id(msg)

        atributos_roupa = {
            "categoria": categorias,
            "cor": cores,
            "detalhe": detalhes,
            "tamanho": tamanhos,
        }
        produto = self._montar_produto_roupa(atributos_roupa)
        if produto is None and pedido_id is None:
            produto = self._extrair_produto_generico(msg, tokens)

        return {
            "numeros": re.findall(r"\b\d+(?:[.,]\d+)?\b", msg or ""),
            "valores_monetarios": valores,
            "quantidade": quantidade,
            "cliente": self._extrair_cliente(msg),
            "fornecedor": self._extrair_fornecedor(msg),
            "telefone": self._extrair_telefone(msg),
            "endereco": self._extrair_endereco(msg),
            "endereco_fornecedor": self._extrair_endereco_fornecedor(msg),
            "observacao_cliente": self._extrair_observacao_cliente(msg),
            "observacao_fornecedor": self._extrair_observacao_fornecedor(msg),
            "descricao_financeira": self._extrair_descricao_financeira(msg),
            "categoria_financeira": self._extrair_categoria_financeira(tokens),
            "pedido_id": pedido_id,
            "edicao_pedido": self._extrair_edicao_pedido(
                tokens=tokens,
                produto=produto,
                atributos=atributos_roupa,
                quantidade=quantidade,
                valores=valores,
            ),
            "memoria_texto": self._extrair_memoria_texto(msg),
            "busca_memoria": self._extrair_busca_memoria(msg),
            "termo_busca": self._extrair_termo_busca(msg),
            "formato_exportacao": self._extrair_formato_exportacao(tokens),
            "fase_memoria": self._extrair_fase_memoria(tokens),
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

    def _extrair_tamanhos(self, tokens: list[str]) -> list[str]:
        tamanhos = []
        for indice, token in enumerate(tokens):
            if token not in self.TAMANHOS:
                continue

            if token.replace(",", ".").replace(".", "", 1).isdigit():
                if self._parece_numero_monetario(tokens, indice):
                    continue

            if token not in tamanhos:
                tamanhos.append(token)

        return tamanhos

    def _parece_numero_monetario(self, tokens: list[str], indice: int) -> bool:
        anterior = tokens[indice - 1] if indice >= 1 else ""
        dois_antes = tokens[indice - 2] if indice >= 2 else ""

        if anterior in {
            "por",
            "r$",
            "valor",
            "preco",
            "custo",
            "paguei",
            "pagou",
            "recebi",
            "deve",
            "devendo",
        }:
            return True

        if anterior == "de" and dois_antes in {"valor", "preco", "custo"}:
            return True

        return False

    def _extrair_valores_monetarios(self, msg: str) -> list[str]:
        texto = msg or ""
        valores = re.findall(r"R\$\s*\d+(?:[.,]\d+)?", texto, flags=re.IGNORECASE)
        valores.extend(
            re.findall(
                r"\b(?:por|para|valor(?: de)?|no valor de|preco(?: de)?|custo(?: de)?|custa|custar|custou|costar|costou|despesa(?: com| de)?|entrada(?: de)?|gastei|gasto(?: com| de)?|pagamento(?: de)?|paguei|deve|devendo|pagou|pago|recebi|recebido|retirei|saida(?: de)?|saiu|entrou|coloquei|tirei)\s*(?:uns?\s*)?(?:r\$\s*)?(\d+(?:[.,]\d+)?)",
                self._normalizar(texto),
            )
        )
        valores.extend(
            re.findall(
                r"\b(?:despesa|gasto|gastei|paguei)\b.+?(?:r\$\s*)?(\d+(?:[.,]\d+)?)\b",
                self._normalizar(texto),
            )
        )
        return valores

    def _extrair_pedido_id(self, msg: str) -> str | None:
        texto = self._normalizar(msg)
        encontrado = re.search(r"(?:^|\s)#\s*(\d+)\b", texto)
        if encontrado:
            return encontrado.group(1)

        encontrado = re.search(r"\bpedido\s*#?\s*(\d+)\b", texto)
        if encontrado:
            return encontrado.group(1)

        encontrado = re.search(r"\bpedido\s+(?:n|numero|num)\s*\.?\s*(\d+)\b", texto)
        if encontrado:
            return encontrado.group(1)

        return None

    def _extrair_edicao_pedido(
        self,
        tokens: list[str],
        produto: str | None,
        atributos: dict[str, list[str]],
        quantidade: str | None,
        valores: list[str],
    ) -> dict[str, Any]:
        conjunto = set(tokens)
        edicao: dict[str, Any] = {}
        valor = valores[-1] if valores else None

        if valor and conjunto & {"preco", "valor", "venda", "cobrar"}:
            edicao["preco_venda"] = valor

        if valor and conjunto & {"custo", "compra", "comprei", "paguei"}:
            edicao["custo_compra"] = valor

        if conjunto & {"quantidade", "qtd"}:
            if quantidade:
                edicao["quantidade"] = quantidade
            elif valor:
                edicao["quantidade"] = valor

        if produto and (conjunto & {"produto", "peca"} or atributos.get("categoria")):
            edicao["produto"] = produto

        novos_atributos: dict[str, list[str]] = {}
        for campo in ("categoria", "cor", "detalhe", "tamanho"):
            valores_campo = atributos.get(campo) or []
            if valores_campo:
                novos_atributos[campo] = valores_campo

        if novos_atributos and conjunto & {
            "categoria",
            "cor",
            "detalhe",
            "modelo",
            "produto",
            "tamanho",
            "peca",
        }:
            edicao["atributos"] = novos_atributos

        return edicao

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

        procura = re.search(
            r"^\s*(\w+)\s+(?:quer|queria|pediu)\b.*\b(?:ver|veja|procurar|procura|achar|ache|olhar)\b",
            texto,
            flags=re.IGNORECASE,
        )
        if procura:
            cliente = procura.group(1).strip()
            if self._cliente_valido(cliente):
                return cliente.capitalize()

        padroes = [
            r"\b(?:moletom|moleton)\s+(?:da|do|de)\s+(\w+)",
            r"\b(?:cadastrar|cadastre|cadastro)\s+(?:cliente\s+)?(\w+)",
            r"\b(?:telefone|telefones|whatsapp|zap|celular|contato|dados|endereco|enderecos|cadastro)\s+(?:da|do|de)\s+(\w+)",
            r"\b(?:anota|anote|anotar|observacao|obs)\s+(?:no\s+)?(?:cliente\s+)?(\w+)",
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

    def _extrair_fornecedor(self, msg: str) -> str | None:
        texto = msg or ""
        padroes = [
            r"\b(?:cadastrar|cadastre|cadastro)\s+(?:o\s+)?(?:fornecedor|fornecedora)\s+(.+?)(?=\s+(?:telefone|whatsapp|zap|celular|contato|endereco|vende|vendem|fornece|fornecem|produto|produtos|que|por|com|e|eh)\b|$)",
            r"\b(?:fornecedor|fornecedora)\s+(.+?)(?=\s+(?:telefone|whatsapp|zap|celular|contato|endereco|vende|vendem|fornece|fornecem|produto|produtos|que|por|com|e|eh)\b|$)",
            r"\b(?:telefone|telefones|whatsapp|zap|celular|contato|dados|endereco|enderecos)\s+(?:do|da|de)\s+(?:fornecedor|fornecedora)\s+(.+?)(?=\s+(?:e|eh|para|fica|:)\b|$)",
            r"\b(?:anota|anote|anotar|observacao|obs)\s+(?:no|na|do|da|de)\s+(?:fornecedor|fornecedora)\s+(.+?)(?=\s+(?:que|:)\b|$)",
        ]

        for padrao in padroes:
            encontrado = re.search(padrao, texto, flags=re.IGNORECASE)
            if not encontrado:
                continue

            fornecedor = self._limpar_nome_fornecedor(encontrado.group(1))
            if fornecedor and self._fornecedor_valido(fornecedor):
                return fornecedor

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

    def _fornecedor_valido(self, fornecedor: str) -> bool:
        palavra = self._normalizar(fornecedor)
        return palavra not in {
            "calcinha",
            "calca",
            "camisa",
            "camiseta",
            "cliente",
            "comprar",
            "fornecedor",
            "produto",
            "produtos",
        }

    def _limpar_nome_fornecedor(self, fornecedor: str) -> str:
        nome = " ".join((fornecedor or "").strip(" .,:;").split())
        if not nome:
            return ""

        normalizado = self._normalizar(nome)
        if normalizado.startswith(("da ", "de ", "do ")):
            return ""

        palavras_descartadas = {
            "a",
            "as",
            "o",
            "os",
            "um",
            "uma",
            "uns",
            "umas",
        }
        partes = [
            parte
            for parte in nome.split()
            if self._normalizar(parte) not in palavras_descartadas
        ]
        return " ".join(parte.capitalize() for parte in partes)

    def _extrair_telefone(self, msg: str) -> str | None:
        texto = self._normalizar(msg)
        padroes = [
            r"\b(?:telefone|whatsapp|zap|celular|contato)\s+(?:da|do|de)\s+(?:cliente|fornecedor|fornecedora)?\s*[\w\s.-]+?\s*(?:e|eh|para|:)\s*((?:\+?\d[\d\s().-]{6,}\d))",
            r"\b(?:telefone|whatsapp|zap|celular|contato)(?:\s+(?:da|do|de)\s+\w+)?\s*(?:e|eh|para|:)?\s*((?:\+?\d[\d\s().-]{6,}\d))",
            r"\b(?:telefone|whatsapp|zap|celular|contato)\s+(\d{8,})\b",
        ]

        for padrao in padroes:
            encontrado = re.search(padrao, texto, flags=re.IGNORECASE)
            if not encontrado:
                continue

            telefone = re.sub(r"\D+", "", encontrado.group(1))
            if len(telefone) >= 8:
                return telefone

        return None

    def _extrair_endereco(self, msg: str) -> str | None:
        texto = self._normalizar(msg)
        padroes = [
            r"\b(?:endereco|enderecos)\s+(?:da|do|de)\s+\w+\s*(?:e|eh|para|fica|:)?\s*(.+)$",
            r"\b(?:endereco|enderecos)\s*(?:e|eh|para|fica|:)?\s*(.+)$",
            r"\bmora\s+(?:na|no|em)\s+(.+)$",
        ]

        for padrao in padroes:
            encontrado = re.search(padrao, texto, flags=re.IGNORECASE)
            if not encontrado:
                continue

            endereco = encontrado.group(1).strip(" .,:;")
            endereco = re.split(
                r"\b(?:telefone|whatsapp|zap|celular|contato)\b",
                endereco,
                maxsplit=1,
            )[0].strip(" .,:;")
            if endereco and endereco not in {"e", "eh", "para"}:
                return endereco

        return None

    def _extrair_endereco_fornecedor(self, msg: str) -> str | None:
        texto = self._normalizar(msg)
        padroes = [
            r"\b(?:endereco|enderecos)\s+(?:do|da|de)\s+(?:fornecedor|fornecedora)\s+.+?\s+(?:e|eh|para|fica|:)\s*(.+)$",
            r"\b(?:fornecedor|fornecedora)\s+.+?\s+(?:endereco|fica)\s*(?:na|no|em|e|eh|para|:)?\s*(.+)$",
        ]

        for padrao in padroes:
            encontrado = re.search(padrao, texto, flags=re.IGNORECASE)
            if not encontrado:
                continue

            endereco = encontrado.group(1).strip(" .,:;")
            endereco = re.split(
                r"\b(?:telefone|whatsapp|zap|celular|contato)\b",
                endereco,
                maxsplit=1,
            )[0].strip(" .,:;")
            if endereco and endereco not in {"e", "eh", "para"}:
                return endereco

        return None

    def _extrair_observacao_cliente(self, msg: str) -> str | None:
        texto = self._normalizar(msg)
        padroes = [
            r"\b(?:anota|anote|anotar|observacao|obs)\b.*?\b(?:que|:)\s*(.+)$",
            r"\b(?:anota|anote|anotar|observacao|obs)\s+(?:no\s+)?(?:cliente\s+)?\w+\s+(.+)$",
            r"\bcliente\s+\w+\s+((?:gosta|prefere|paga|usa|mora|veste)\b.+)$",
        ]

        for padrao in padroes:
            encontrado = re.search(padrao, texto, flags=re.IGNORECASE)
            if encontrado:
                observacao = encontrado.group(1).strip(" .,:;")
                return observacao or None

        return None

    def _extrair_observacao_fornecedor(self, msg: str) -> str | None:
        texto = self._normalizar(msg)
        padroes = [
            r"\b(?:anota|anote|anotar|observacao|obs)\b.*?\b(?:que|:)\s*(.+)$",
            r"\b(?:fornecedor|fornecedora)\s+.+?\s+((?:aceita|atende|entrega|prefere|trabalha)\b.+)$",
        ]

        for padrao in padroes:
            encontrado = re.search(padrao, texto, flags=re.IGNORECASE)
            if encontrado:
                observacao = encontrado.group(1).strip(" .,:;")
                return observacao or None

        return None

    def _extrair_descricao_financeira(self, msg: str) -> str | None:
        texto = self._normalizar(msg)
        numero = r"(?:r\$\s*)?\d+(?:[.,]\d+)?"
        padroes = [
            rf"\b(?:gastei|paguei)\s+{numero}\s+(?:com|em|no|na|num|numa|para|pra|pro)?\s*(.+)$",
            rf"\b(?:gastei|paguei)\s+(.+?)\s+{numero}\b",
            rf"\b(?:despesa|gasto)\s+(?:com|de)?\s*(.+?)\s+{numero}\b",
            rf"\b(?:despesa|gasto)\s+(?:com|de)?\s*(.+)$",
            rf"\b(?:saiu|retirei|tirei)\s+{numero}\s+(?:do|da)?\s*caixa\s*(?:para|pra|pro|com)?\s*(.+)$",
            rf"\b(?:entrou|coloquei|recebi)\s+{numero}\s+(?:no|na)?\s*caixa\s*(?:de|do|da|por|para|pra|pro)?\s*(.+)$",
        ]

        for padrao in padroes:
            encontrado = re.search(padrao, texto, flags=re.IGNORECASE)
            if not encontrado:
                continue

            descricao = self._limpar_descricao_financeira(encontrado.group(1))
            if descricao:
                return descricao

        return None

    def _extrair_categoria_financeira(self, tokens: list[str]) -> str | None:
        categorias = {
            "embalagem": {"embalagem", "embalagens", "sacola", "sacolas", "etiqueta"},
            "transporte": {
                "entrega",
                "frete",
                "gasolina",
                "motoboy",
                "transporte",
                "uber",
            },
            "marketing": {"anuncio", "anuncios", "instagram", "marketing", "trafego"},
            "fixo": {"agua", "aluguel", "internet", "luz"},
            "taxa": {"maquininha", "tarifa", "taxa", "taxas"},
            "compra": {"compra", "mercadoria", "mercadorias", "peca", "pecas"},
        }
        conjunto = set(tokens)
        for categoria, palavras in categorias.items():
            if conjunto & palavras:
                return categoria
        return None

    def _limpar_descricao_financeira(self, descricao: str) -> str:
        palavras_descartadas = {
            "a",
            "as",
            "caixa",
            "com",
            "da",
            "de",
            "do",
            "e",
            "em",
            "na",
            "no",
            "o",
            "os",
            "para",
            "pra",
            "pro",
            "r$",
            "reais",
            "real",
        }
        partes = []
        for parte in (descricao or "").split():
            palavra = self._normalizar(parte.strip(".,;:?!"))
            if not palavra:
                continue
            if palavra.startswith("r$"):
                continue
            if palavra.replace(",", ".").replace(".", "", 1).isdigit():
                continue
            if palavra in palavras_descartadas:
                continue
            partes.append(palavra)

        return " ".join(partes).strip()

    def _extrair_memoria_texto(self, msg: str) -> str | None:
        texto = self._normalizar(msg)
        encontrado = re.search(
            r"\b(?:guarde|guardar|lembre|memoriza|memorizar|memorize)\s+(?:que\s+)?(.+)$",
            texto,
            flags=re.IGNORECASE,
        )
        if encontrado:
            return encontrado.group(1).strip()

        for padrao in (
            r"^(?:minha|minhas|meu|meus)?\s*metas?\b.+$",
            r"^(?:minha|minhas|meu|meus)?\s*estrategias?\b.+$",
            r"^(?:minha|minhas|meu|meus)?\s*preferencias?\b.+$",
            r"^prefiro\b.+$",
            r"^(?:minha|minhas|meu|meus)?\s*regras?\b.+$",
            r"^fornecedores?\b.+$",
        ):
            if re.search(padrao, texto, flags=re.IGNORECASE):
                return texto

        return None

    def _extrair_busca_memoria(self, msg: str) -> str | None:
        texto = self._normalizar(msg)
        padroes = [
            r"\b(?:apague|apagar|esqueca|esquecer)\s+(?:que\s+)?(.+)$",
            r"\b(?:memoria|memorias|lembra|lembrar)\s+(?:sobre|de)\s+(.+)$",
        ]

        for padrao in padroes:
            encontrado = re.search(padrao, texto, flags=re.IGNORECASE)
            if encontrado:
                return encontrado.group(1).strip()

        return None

    def _extrair_formato_exportacao(self, tokens: list[str]) -> str:
        conjunto = set(tokens)
        if conjunto & {"csv", "excel", "planilha"}:
            return "csv"

        return "json"

    def _extrair_termo_busca(self, msg: str) -> str | None:
        texto = self._normalizar(msg)
        encontrado = re.search(
            r"\b(?:achar|ache|busca|buscar|encontra|encontrar|encontre|localiza|localizar|localize|pesquisa|pesquisar|procura|procurar|procure)\s+(?:por\s+)?(.+)$",
            texto,
            flags=re.IGNORECASE,
        )
        if not encontrado:
            return None

        termo = encontrado.group(1).strip(" .,:;")
        termo = self._limpar_termo_busca(termo)
        return termo or None

    def _limpar_termo_busca(self, termo: str) -> str:
        descartadas_inicio = {
            "a",
            "as",
            "cliente",
            "clientes",
            "da",
            "das",
            "de",
            "do",
            "dos",
            "fornecedor",
            "fornecedora",
            "fornecedores",
            "n",
            "numero",
            "o",
            "os",
            "pedido",
            "pedidos",
            "produto",
            "produtos",
        }
        partes = [
            parte.strip(" .,:;?!")
            for parte in (termo or "").split()
            if parte.strip(" .,:;?!")
        ]

        while partes and self._normalizar(partes[0]) in descartadas_inicio:
            partes.pop(0)

        return " ".join(partes).strip()

    def _extrair_fase_memoria(self, tokens: list[str]) -> int | None:
        conjunto = set(tokens)

        if conjunto & {"contexto", "imediato"}:
            return 1

        if conjunto & {"historico", "conversa"}:
            return 2

        if conjunto & {
            "loja",
            "operacional",
            "operacionais",
            "fornecedor",
            "fornecedores",
            "preferencia",
            "preferencias",
            "prefiro",
            "regra",
            "regras",
        }:
            return 3

        if conjunto & {
            "aprendido",
            "aprendidos",
            "aprendizado",
            "aprendizados",
            "apelido",
            "apelidos",
            "padrao",
            "padroes",
            "uso",
        }:
            return 4

        if conjunto & {
            "estrategia",
            "estrategica",
            "estrategicas",
            "estrategico",
            "estrategicos",
            "meta",
            "metas",
            "previsao",
            "previsoes",
            "sugestao",
            "sugestoes",
            "tendencia",
            "tendencias",
        }:
            return 5

        for indice, token in enumerate(tokens[:-1]):
            if token != "fase":
                continue
            proximo = tokens[indice + 1]
            if proximo.isdigit() and 1 <= int(proximo) <= 5:
                return int(proximo)

        return None

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
        if tokens and tokens[0] in self.TERMOS_BUSCA:
            return None

        produto = self._extrair_produto_por_marcador(msg)
        if produto:
            return produto

        indices_valor = {
            indice
            for indice, token in enumerate(tokens)
            if token in {
                "caixa",
                "custo",
                "despesa",
                "entrou",
                "gastei",
                "gasto",
                "paguei",
                "por",
                "preco",
                "retirei",
                "saiu",
                "valor",
            }
        }
        palavras_descartadas = {
            "caixa",
            "comprei",
            "compramos",
            "despesa",
            "despesas",
            "entrou",
            "gastei",
            "gasto",
            "gastos",
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
            "retirei",
            "quanto",
            "saiu",
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
