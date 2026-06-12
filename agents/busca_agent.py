"""Agente de busca geral do Cooper."""

from typing import Any

from agents.base_agent import BaseAgent
from repositories.clientes_repository import ClientesRepository
from repositories.estoque_repository import EstoqueRepository
from repositories.fornecedores_repository import FornecedoresRepository
from repositories.pedidos_repository import PedidosRepository


class BuscaAgent(BaseAgent):
    """Agente responsavel por busca geral nos dados da loja."""

    PALAVRAS_CHAVE = {
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

    def __init__(
        self,
        clientes_repository: ClientesRepository | None = None,
        pedidos_repository: PedidosRepository | None = None,
        fornecedores_repository: FornecedoresRepository | None = None,
        estoque_repository: EstoqueRepository | None = None,
    ) -> None:
        super().__init__(nome="busca")
        self.clientes_repository = clientes_repository or ClientesRepository()
        self.pedidos_repository = pedidos_repository or PedidosRepository()
        self.fornecedores_repository = (
            fornecedores_repository or FornecedoresRepository()
        )
        self.estoque_repository = estoque_repository or EstoqueRepository()

    def pode_processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> bool:
        if analise:
            return analise.get("dominio") == "busca"

        texto = (msg or "").lower()
        return any(palavra in texto for palavra in self.PALAVRAS_CHAVE)

    def processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        intencao = str((analise or {}).get("intencao") or "busca_geral")
        entidades = self.entidades(analise)
        termo = self._termo_busca(entidades)
        resultado = self._buscar(termo) if termo else None

        dados = {
            "mensagem_original": msg,
            "resumo": self._resumo(intencao),
            "acao": "buscar_dados_da_loja",
            "termo": termo,
            "entidades": entidades,
            "campos_necessarios": [] if termo else ["termo_de_busca"],
            "proximas_acoes": ["abrir o cadastro encontrado", "seguir o pedido"],
            "resultado": resultado,
        }

        return self.resposta_padrao(status="sucesso", tipo=intencao, dados=dados)

    def _resumo(self, intencao: str) -> str:
        resumos = {
            "busca_geral": "Busca geral realizada.",
        }
        return resumos.get(intencao, "Busca identificada.")

    def _buscar(self, termo: str) -> dict[str, Any]:
        clientes = self.clientes_repository.buscar_por_termo(termo, limite=5)
        pedidos = self.pedidos_repository.buscar_por_termo(termo, limite=8)
        fornecedores = self.fornecedores_repository.buscar_por_termo(
            termo,
            limite=5,
        )
        produtos_fornecedor = self.fornecedores_repository.buscar_produtos_por_termo(
            termo,
            limite=8,
        )
        produtos_estoque = self.estoque_repository.buscar_por_termo(termo, limite=8)
        total = sum(
            len(itens)
            for itens in (
                clientes,
                pedidos,
                fornecedores,
                produtos_fornecedor,
                produtos_estoque,
            )
        )

        return {
            "tipo_resultado": "busca_resultados",
            "termo": termo,
            "total": total,
            "clientes": clientes,
            "pedidos": pedidos,
            "fornecedores": fornecedores,
            "produtos_fornecedor": produtos_fornecedor,
            "produtos_estoque": produtos_estoque,
        }

    def _termo_busca(self, entidades: dict[str, Any]) -> str | None:
        for chave in ("termo_busca", "cliente", "fornecedor", "produto"):
            valor = entidades.get(chave)
            if valor:
                termo = " ".join(str(valor).strip().split())
                if termo:
                    return termo

        pedido_id = entidades.get("pedido_id")
        if pedido_id:
            return str(pedido_id)

        return None
