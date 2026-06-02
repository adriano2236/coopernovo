# core/router.py

from agents.compras_agent import ComprasAgent
from agents.vendas_agent import VendasAgent
from agents.estoque_agent import EstoqueAgent
from agents.resumo_agent import ResumoAgent
from agents.atualizar_agent import AtualizarAgent


class Router:
    def __init__(self, actions, contexto, tasks, event_bus):
        self.actions = actions
        self.contexto = contexto
        self.tasks = tasks
        self.event_bus = event_bus

        self.routes = {}

        self.agentes = {
            "compra": ComprasAgent(self.event_bus),
            "venda": VendasAgent(self.event_bus),
            "estoque": EstoqueAgent(),
            "resumo": ResumoAgent(),
            "atualizar": AtualizarAgent(),
        }

    # -------------------------
    # PROCESSAMENTO PRINCIPAL
    # -------------------------
    def processar(self, msg: str):
        msg_lower = msg.lower().strip()

                # Saudação
        if msg_lower in [
            "oi",
            "ola",
            "olá",
            "bom dia",
            "boa tarde",
            "boa noite"
        ]:
            return "Olá! Como posso ajudar?"

        # Despedida
        if msg_lower in [
            "tchau",
            "sair",
            "fim",
            "encerrar",
            "desligar"
        ]:
            return "Até logo!"

        # Ações diretas
        if msg_lower in self.routes:
            return self.routes[msg_lower]()

        # NLP
        analise = self.contexto.analisar(msg_lower)
        intencao = analise["intencao"]

        # Agentes
        if intencao in self.agentes:
            resposta = self.agentes[intencao].processar(msg)

            self.contexto.registrar(
                msg,
                resposta,
                analise
            )

            return resposta

        # Fallback
        return self._fallback(msg_lower)

    # -------------------------
    # FALLBACK
    # -------------------------
    def _fallback(self, msg):
        return (
            "Não entendi. "
            "Tente: compra, venda, estoque, resumo ou atualizar."
        )