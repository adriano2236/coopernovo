# core/cooper.py

from core.context import Contexto
from core.tasks import TaskManager
from core.event_bus import EventBus
from core.logger import CooperLogger

from core.actions.action_bus import ActionBus
from core.actions.system_actions import status_cooper

from core.router import Router


class Cooper:
    def __init__(self):
        self.logger = CooperLogger()
        self.event_bus = EventBus()
        self.tasks = TaskManager()
        self.contexto = Contexto()

        self.actions = ActionBus()

        # Ações do sistema
        self.actions.registrar("status", status_cooper)
        self.actions.registrar("backup", self._backup)
        self.actions.registrar("produtos", self._produtos)
        self.actions.registrar("estoque_baixo", self._estoque_baixo_action)

        # Eventos
        self.event_bus.registrar("venda_realizada", self._on_venda)
        self.event_bus.registrar("compra_realizada", self._on_compra)
        self.event_bus.registrar("estoque_baixo", self._on_estoque_baixo)

        # Router passa a controlar agentes e decisões
        self.router = Router(
            actions=self.actions,
            contexto=self.contexto,
            tasks=self.tasks,
            event_bus=self.event_bus
        )

        self.logger.info("Cooper inicializado")

    def processar(self, msg):
        return self.router.processar(msg)

    def _on_venda(self, evento, dados):
        self.logger.acao(
            "VENDA",
            f"{dados['quantidade']} {dados['produto']} por R$ {dados['preco']}"
        )

    def _on_compra(self, evento, dados):
        self.logger.acao(
            "COMPRA",
            f"{dados['quantidade']} {dados['produto']} por R$ {dados['preco']}"
        )

    def _on_estoque_baixo(self, evento, dados):
        self.logger.warning(
            f"⚠️ Estoque baixo: {dados['produto']} ({dados['estoque']} un)"
        )

    def _backup(self):
        return "Backup executado (placeholder)"

    def _produtos(self):
        return "Lista de produtos (placeholder)"

    def _estoque_baixo_action(self):
        return "Estoque baixo acionado (placeholder)"