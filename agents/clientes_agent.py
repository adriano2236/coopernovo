"""Agente de clientes do Cooper."""

from typing import Any

from agents.base_agent import BaseAgent
from repositories.clientes_repository import ClientesRepository


class ClientesAgent(BaseAgent):
    """Agente responsavel pelo cadastro e consulta de clientes."""

    PALAVRAS_CHAVE = {
        "cadastro",
        "cadastrar",
        "cadastre",
        "cliente",
        "clientes",
        "contato",
        "dados",
        "endereco",
        "telefone",
        "whatsapp",
    }

    def __init__(self, repository: ClientesRepository | None = None) -> None:
        super().__init__(nome="clientes")
        self.repository = repository or ClientesRepository()

    def pode_processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> bool:
        if analise:
            return analise.get("dominio") == "clientes"

        texto = (msg or "").lower()
        return any(palavra in texto for palavra in self.PALAVRAS_CHAVE)

    def processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        intencao = str((analise or {}).get("intencao") or "clientes_consultar")
        entidades = self.entidades(analise)
        cliente = entidades.get("cliente")
        telefone = entidades.get("telefone")
        endereco = entidades.get("endereco")
        observacao = entidades.get("observacao_cliente")

        resultado = self._executar_acao(
            intencao=intencao,
            cliente=cliente,
            telefone=telefone,
            endereco=endereco,
            observacao=observacao,
        )

        dados = {
            "mensagem_original": msg,
            "resumo": self._resumo(intencao),
            "acao": self._acao(intencao),
            "cliente": cliente,
            "telefone": telefone,
            "endereco": endereco,
            "observacao": observacao,
            "entidades": entidades,
            "campos_necessarios": self._campos_necessarios(
                intencao=intencao,
                cliente=cliente,
                telefone=telefone,
                endereco=endereco,
                observacao=observacao,
            ),
            "proximas_acoes": self._proximas_acoes(intencao),
            "resultado": resultado,
        }

        return self.resposta_padrao(status="sucesso", tipo=intencao, dados=dados)

    def _resumo(self, intencao: str) -> str:
        resumos = {
            "clientes_criar": "Cliente cadastrado.",
            "clientes_atualizar": "Cliente atualizado.",
            "clientes_consultar": "Cadastro do cliente consultado.",
            "clientes_listar": "Clientes cadastrados recuperados.",
            "clientes_anotar": "Observacao do cliente registrada.",
        }
        return resumos.get(intencao, "Solicitacao de cliente identificada.")

    def _acao(self, intencao: str) -> str:
        acoes = {
            "clientes_criar": "cadastrar_cliente",
            "clientes_atualizar": "atualizar_cliente",
            "clientes_consultar": "consultar_cliente",
            "clientes_listar": "listar_clientes",
            "clientes_anotar": "anotar_cliente",
        }
        return acoes.get(intencao, "analisar_cliente")

    def _campos_necessarios(
        self,
        intencao: str,
        cliente: str | None,
        telefone: str | None,
        endereco: str | None,
        observacao: str | None,
    ) -> list[str]:
        if intencao == "clientes_listar":
            return []

        campos = []
        if not cliente:
            campos.append("cliente")

        if intencao == "clientes_criar" and not any(
            (telefone, endereco, observacao)
        ):
            campos.append("telefone_endereco_ou_observacao")

        if intencao == "clientes_atualizar" and not any((telefone, endereco)):
            campos.append("telefone_ou_endereco")

        if intencao == "clientes_anotar" and not observacao:
            campos.append("observacao")

        return campos

    def _proximas_acoes(self, intencao: str) -> list[str]:
        proximas = {
            "clientes_criar": ["usar cliente nos pedidos"],
            "clientes_atualizar": ["manter cadastro correto"],
            "clientes_consultar": ["consultar historico de pedidos"],
            "clientes_listar": ["selecionar cliente para atendimento"],
            "clientes_anotar": ["usar observacao em vendas futuras"],
        }
        return proximas.get(intencao, ["organizar clientes"])

    def _executar_acao(
        self,
        intencao: str,
        cliente: str | None,
        telefone: str | None,
        endereco: str | None,
        observacao: str | None,
    ) -> dict[str, Any] | None:
        if intencao == "clientes_listar":
            return {
                "tipo_resultado": "clientes_lista",
                "itens": self.repository.listar_clientes(),
            }

        if not cliente:
            return None

        if intencao == "clientes_consultar":
            encontrado = self.repository.buscar_por_nome(cliente)
            return encontrado or self._cliente_nao_encontrado(cliente)

        if intencao == "clientes_anotar":
            return self._anotar_cliente(cliente, observacao)

        if intencao in {"clientes_criar", "clientes_atualizar"}:
            return self.repository.salvar_cliente(
                nome=cliente,
                telefone=telefone,
                endereco=endereco,
                observacoes=observacao,
            )

        return None

    def _anotar_cliente(
        self,
        cliente: str,
        observacao: str | None,
    ) -> dict[str, Any] | None:
        if not observacao:
            encontrado = self.repository.buscar_por_nome(cliente)
            return encontrado or self._cliente_nao_encontrado(cliente)

        existente = self.repository.buscar_por_nome(cliente)
        observacoes = self._juntar_observacoes(
            atual=(existente or {}).get("observacoes"),
            nova=observacao,
        )
        return self.repository.salvar_cliente(
            nome=cliente,
            observacoes=observacoes,
        )

    def _juntar_observacoes(self, atual: str | None, nova: str) -> str:
        nota = " ".join((nova or "").strip().split())
        if not atual:
            return nota

        if nota.lower() in atual.lower():
            return atual

        return f"{atual} | {nota}"

    def _cliente_nao_encontrado(self, cliente: str) -> dict[str, Any]:
        return {
            "tipo_resultado": "cliente_nao_encontrado",
            "cliente": cliente,
        }
