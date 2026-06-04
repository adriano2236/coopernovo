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

        print(f"[NLP] {analise}")

        intencao = analise["intencao"]

        if (
            intencao == "desconhecido"
            and analise["entidades"].get("referencia")
        ):
            intencao = self.contexto.contexto["estado_atual"]["ultima_intencao"]

            print(f"[INTENCAO_FINAL] {intencao}")

        # Agentes
        if intencao in self.agentes:

            print(f"[ROUTER] Agente selecionado: {intencao}")

            resposta = self.agentes[intencao].processar(
                msg,
                analise
            )

            self.contexto.registrar(
                msg,
                resposta,
                analise
        )

            return {
                "agente": intencao,
                "resposta": resposta,
                "analise": analise
            }

    # -------------------------
    # FALLBACK
    # -------------------------
    def _fallback(self, msg):
        msg = msg.lower()
    
        if any(p in msg for p in ["vendi", "vende", "venda"]):
            return (
                "Entendi que você quer registrar uma venda. "
                "Exemplo: vendi 2 calcinha codigo 720 por 25 reais"
            )
    
        if any(p in msg for p in ["comprei", "compra", "comprar"]):
            return (
                "Entendi que você quer registrar uma compra. "
                "Exemplo: comprei 5 calcinha codigo 720 por 10 reais"
            )
    
        if any(p in msg for p in ["estoque", "produto", "codigo"]):
            return (
                "Você pode consultar o estoque dizendo: estoque"
            )
    
        return (
            "Não entendi o comando.\n"
            "Exemplos:\n"
            "- comprei 5 calcinha codigo 720 por 10 reais\n"
            "- vendi 2 calcinha codigo 720 por 25 reais\n"
            "- estoque\n"
            "- resumo"
        )