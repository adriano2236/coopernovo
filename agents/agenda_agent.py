"""Agente de agenda operacional do Cooper."""

from typing import Any

from agents.base_agent import BaseAgent
from repositories.contas_repository import ContasRepository
from repositories.pedidos_repository import PedidosRepository


class AgendaAgent(BaseAgent):
    """Agente responsavel por organizar as proximas acoes da loja."""

    PALAVRAS_CHAVE = {
        "agenda",
        "afazeres",
        "fazer",
        "pendencia",
        "pendencias",
        "preciso",
        "prioridade",
        "prioridades",
        "tarefas",
    }

    def __init__(
        self,
        pedidos_repository: PedidosRepository | None = None,
        contas_repository: ContasRepository | None = None,
    ) -> None:
        super().__init__(nome="agenda")
        self.pedidos_repository = pedidos_repository or PedidosRepository()
        self.contas_repository = contas_repository or ContasRepository()

    def pode_processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> bool:
        if analise:
            return analise.get("dominio") == "agenda"

        texto = (msg or "").lower()
        return any(palavra in texto for palavra in self.PALAVRAS_CHAVE)

    def processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        intencao = str((analise or {}).get("intencao") or "agenda_hoje")
        dias_parado = self._dias_parado(analise)
        resultado = self._montar_agenda(dias_parado=dias_parado)

        dados = {
            "mensagem_original": msg,
            "resumo": self._resumo(intencao),
            "acao": self._acao(intencao),
            "dias_parado": dias_parado,
            "entidades": self.entidades(analise),
            "campos_necessarios": [],
            "proximas_acoes": ["executar prioridades da loja"],
            "resultado": resultado,
        }

        return self.resposta_padrao(status="sucesso", tipo=intencao, dados=dados)

    def _resumo(self, intencao: str) -> str:
        resumos = {
            "agenda_hoje": "Agenda operacional da loja montada.",
        }
        return resumos.get(intencao, "Solicitacao de agenda identificada.")

    def _acao(self, intencao: str) -> str:
        acoes = {
            "agenda_hoje": "montar_agenda_operacional",
        }
        return acoes.get(intencao, "analisar_agenda")

    def _montar_agenda(self, dias_parado: int) -> dict[str, Any]:
        para_procurar = self._enriquecer_pedidos(
            self.pedidos_repository.listar_pedidos_para_procurar()
        )
        para_comprar = self._enriquecer_pedidos(
            self.pedidos_repository.listar_compras_pendentes()
        )
        para_cobrar = self._enriquecer_pedidos(
            self.pedidos_repository.listar_pedidos_para_cobrar()
        )
        para_entregar = self._enriquecer_pedidos(
            self.pedidos_repository.listar_pedidos_para_entregar()
        )
        parados = self._enriquecer_pedidos(
            self.pedidos_repository.listar_pedidos_parados(dias=dias_parado)
        )
        contas_abertas = self._enriquecer_contas(self.contas_repository.listar_abertas())
        total_acoes = sum(
            len(itens)
            for itens in (
                para_procurar,
                para_comprar,
                para_cobrar,
                para_entregar,
                parados,
                contas_abertas,
            )
        )

        return {
            "tipo_resultado": "agenda_operacional",
            "periodo": "hoje",
            "dias_parado": dias_parado,
            "total_acoes": total_acoes,
            "para_procurar": para_procurar,
            "para_comprar": para_comprar,
            "para_cobrar": para_cobrar,
            "para_entregar": para_entregar,
            "pedidos_parados": parados,
            "contas_abertas": contas_abertas,
        }

    def _enriquecer_pedidos(
        self,
        pedidos: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return [self._enriquecer_pedido(pedido) for pedido in pedidos]

    def _enriquecer_pedido(self, pedido: dict[str, Any]) -> dict[str, Any]:
        preco = pedido.get("preco_venda")
        custo = pedido.get("custo_compra")
        valor_pago = pedido.get("valor_pago")

        if preco is not None:
            pedido["valor_restante"] = max(float(preco) - float(valor_pago or 0), 0)

        if preco is not None and custo is not None:
            pedido["lucro"] = float(preco) - float(custo)

        return pedido

    def _enriquecer_contas(
        self,
        contas: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        for conta in contas:
            total = float(conta.get("valor_total") or 0)
            pago = float(conta.get("valor_pago") or 0)
            conta["valor_restante"] = max(total - pago, 0)
        return contas

    def _dias_parado(self, analise: dict[str, Any] | None) -> int:
        numero = self.primeiro_numero(analise)
        if numero is None:
            return 3

        try:
            dias = int(float(str(numero).replace(",", ".")))
        except ValueError:
            return 3

        return max(dias, 1)
