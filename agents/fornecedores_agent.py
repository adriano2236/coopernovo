"""Agente de fornecedores do Cooper."""

from typing import Any

from agents.base_agent import BaseAgent
from repositories.fornecedores_repository import FornecedoresRepository


class FornecedoresAgent(BaseAgent):
    """Agente responsavel por fornecedores e produtos fornecidos."""

    PALAVRAS_CHAVE = {
        "atacado",
        "cadastro",
        "cadastrar",
        "cadastre",
        "contato",
        "fornecedor",
        "fornecedora",
        "fornecedores",
        "fornece",
        "produto",
        "telefone",
        "vende",
        "whatsapp",
    }

    def __init__(self, repository: FornecedoresRepository | None = None) -> None:
        super().__init__(nome="fornecedores")
        self.repository = repository or FornecedoresRepository()

    def pode_processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> bool:
        if analise:
            return analise.get("dominio") == "fornecedores"

        texto = (msg or "").lower()
        return any(palavra in texto for palavra in self.PALAVRAS_CHAVE)

    def processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        intencao = str((analise or {}).get("intencao") or "fornecedores_consultar")
        entidades = self.entidades(analise)
        fornecedor = entidades.get("fornecedor")
        telefone = entidades.get("telefone")
        endereco = entidades.get("endereco_fornecedor") or entidades.get("endereco")
        observacao = entidades.get("observacao_fornecedor")
        produto = entidades.get("produto")
        atributos = entidades.get("atributos_roupa") or {}
        custo = self._converter_valor(self.primeiro_valor_monetario(analise))

        resultado = self._executar_acao(
            intencao=intencao,
            fornecedor=fornecedor,
            telefone=telefone,
            endereco=endereco,
            observacao=observacao,
            produto=produto,
            atributos=atributos,
            custo=custo,
        )

        dados = {
            "mensagem_original": msg,
            "resumo": self._resumo(intencao),
            "acao": self._acao(intencao),
            "fornecedor": fornecedor,
            "telefone": telefone,
            "endereco": endereco,
            "observacao": observacao,
            "produto": produto,
            "custo": custo,
            "entidades": entidades,
            "campos_necessarios": self._campos_necessarios(
                intencao=intencao,
                fornecedor=fornecedor,
                telefone=telefone,
                endereco=endereco,
                observacao=observacao,
                produto=produto,
            ),
            "proximas_acoes": self._proximas_acoes(intencao),
            "resultado": resultado,
        }

        return self.resposta_padrao(status="sucesso", tipo=intencao, dados=dados)

    def _resumo(self, intencao: str) -> str:
        resumos = {
            "fornecedores_criar": "Fornecedor cadastrado.",
            "fornecedores_atualizar": "Fornecedor atualizado.",
            "fornecedores_consultar": "Cadastro do fornecedor consultado.",
            "fornecedores_listar": "Fornecedores cadastrados recuperados.",
            "fornecedores_anotar": "Observacao do fornecedor registrada.",
            "fornecedores_vincular_produto": "Produto vinculado ao fornecedor.",
            "fornecedores_buscar_produto": "Fornecedores do produto recuperados.",
        }
        return resumos.get(intencao, "Solicitacao de fornecedor identificada.")

    def _acao(self, intencao: str) -> str:
        acoes = {
            "fornecedores_criar": "cadastrar_fornecedor",
            "fornecedores_atualizar": "atualizar_fornecedor",
            "fornecedores_consultar": "consultar_fornecedor",
            "fornecedores_listar": "listar_fornecedores",
            "fornecedores_anotar": "anotar_fornecedor",
            "fornecedores_vincular_produto": "vincular_produto_fornecedor",
            "fornecedores_buscar_produto": "buscar_fornecedores_por_produto",
        }
        return acoes.get(intencao, "analisar_fornecedor")

    def _campos_necessarios(
        self,
        intencao: str,
        fornecedor: str | None,
        telefone: str | None,
        endereco: str | None,
        observacao: str | None,
        produto: str | None,
    ) -> list[str]:
        if intencao == "fornecedores_listar":
            return []

        campos = []
        if intencao == "fornecedores_buscar_produto":
            if not produto:
                campos.append("produto")
            return campos

        if not fornecedor:
            campos.append("fornecedor")

        if intencao == "fornecedores_criar" and not any(
            (telefone, endereco, observacao, produto)
        ):
            campos.append("telefone_endereco_produto_ou_observacao")

        if intencao == "fornecedores_atualizar" and not any((telefone, endereco)):
            campos.append("telefone_ou_endereco")

        if intencao == "fornecedores_anotar" and not observacao:
            campos.append("observacao")

        if intencao == "fornecedores_vincular_produto" and not produto:
            campos.append("produto")

        return campos

    def _proximas_acoes(self, intencao: str) -> list[str]:
        proximas = {
            "fornecedores_criar": ["usar fornecedor nas compras"],
            "fornecedores_atualizar": ["manter contato correto"],
            "fornecedores_consultar": ["consultar produtos fornecidos"],
            "fornecedores_listar": ["selecionar fornecedor para compra"],
            "fornecedores_anotar": ["usar observacao em compras futuras"],
            "fornecedores_vincular_produto": ["buscar fornecedor por produto"],
            "fornecedores_buscar_produto": ["escolher melhor fornecedor"],
        }
        return proximas.get(intencao, ["organizar fornecedores"])

    def _executar_acao(
        self,
        intencao: str,
        fornecedor: str | None,
        telefone: str | None,
        endereco: str | None,
        observacao: str | None,
        produto: str | None,
        atributos: dict[str, Any],
        custo: float | None,
    ) -> dict[str, Any] | None:
        if intencao == "fornecedores_listar":
            return {
                "tipo_resultado": "fornecedores_lista",
                "itens": self.repository.listar_fornecedores(),
            }

        if intencao == "fornecedores_buscar_produto":
            if not produto:
                return None
            return {
                "tipo_resultado": "fornecedores_produto_lista",
                "produto": produto,
                "itens": self.repository.buscar_por_produto(produto),
            }

        if not fornecedor:
            return None

        if intencao == "fornecedores_consultar":
            encontrado = self.repository.buscar_por_nome(fornecedor)
            return encontrado or self._fornecedor_nao_encontrado(fornecedor)

        if intencao == "fornecedores_anotar":
            return self._anotar_fornecedor(fornecedor, observacao)

        if intencao == "fornecedores_vincular_produto":
            if not produto:
                return self.repository.salvar_fornecedor(
                    nome=fornecedor,
                    telefone=telefone,
                    endereco=endereco,
                    observacoes=observacao,
                )
            return self.repository.salvar_produto_fornecedor(
                fornecedor=fornecedor,
                produto=produto,
                atributos=atributos,
                ultimo_custo=custo,
                observacoes=observacao,
            )

        if intencao in {"fornecedores_criar", "fornecedores_atualizar"}:
            return self.repository.salvar_fornecedor(
                nome=fornecedor,
                telefone=telefone,
                endereco=endereco,
                observacoes=observacao,
            )

        return None

    def _anotar_fornecedor(
        self,
        fornecedor: str,
        observacao: str | None,
    ) -> dict[str, Any] | None:
        if not observacao:
            encontrado = self.repository.buscar_por_nome(fornecedor)
            return encontrado or self._fornecedor_nao_encontrado(fornecedor)

        existente = self.repository.buscar_por_nome(fornecedor)
        observacoes = self._juntar_observacoes(
            atual=(existente or {}).get("observacoes"),
            nova=observacao,
        )
        return self.repository.salvar_fornecedor(
            nome=fornecedor,
            observacoes=observacoes,
        )

    def _juntar_observacoes(self, atual: str | None, nova: str) -> str:
        nota = " ".join((nova or "").strip().split())
        if not atual:
            return nota

        if nota.lower() in atual.lower():
            return atual

        return f"{atual} | {nota}"

    def _fornecedor_nao_encontrado(self, fornecedor: str) -> dict[str, Any]:
        return {
            "tipo_resultado": "fornecedor_nao_encontrado",
            "fornecedor": fornecedor,
        }

    def _converter_valor(self, valor: str | None) -> float | None:
        if valor is None:
            return None

        texto = str(valor).lower().replace("r$", "").strip()
        texto = texto.replace(".", "").replace(",", ".")
        try:
            return float(texto)
        except ValueError:
            return None
