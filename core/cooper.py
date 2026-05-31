# core/cooper.py
from agents.compras_agent import ComprasAgent
from agents.vendas_agent import VendasAgent
from agents.estoque_agent import EstoqueAgent
from agents.resumo_agent import ResumoAgent
from agents.atualizar_agent import AtualizarAgent
from core.context import Contexto
from core.tasks import TaskManager
from core.event_bus import EventBus
from core.logger import CooperLogger
from datetime import datetime

class Cooper:
    def __init__(self):
        # Cria serviços
        self.logger = CooperLogger()
        self.event_bus = EventBus()
        self.tasks = TaskManager()
        self.contexto = Contexto()
        
        # Registra ouvintes de eventos
        self.event_bus.registrar("venda_realizada", self._on_venda)
        self.event_bus.registrar("compra_realizada", self._on_compra)
        self.event_bus.registrar("estoque_baixo", self._on_estoque_baixo)
        
        # Injeta event_bus nos agentes
        self.agentes = {
            "compra": ComprasAgent(self.event_bus),
            "venda": VendasAgent(self.event_bus),
            "estoque": EstoqueAgent(),
            "resumo": ResumoAgent(),
            "atualizar": AtualizarAgent(),
        }
        
        self.logger.info("Cooper inicializado")
        self._verificar_rotina()
    
    def _on_venda(self, evento, dados):
        self.logger.acao("VENDA", f"{dados['quantidade']} {dados['produto']} por R$ {dados['preco']}")
    
    def _on_compra(self, evento, dados):
        self.logger.acao("COMPRA", f"{dados['quantidade']} {dados['produto']} por R$ {dados['preco']}")
    
    def _on_estoque_baixo(self, evento, dados):
        self.logger.warning(f"⚠️ Estoque baixo: {dados['produto']} ({dados['estoque']} un)")
    
    def _verificar_rotina(self):
        from database.db import Database
        db = Database()
        produtos = db.obter_estoque()
        
        tarefas_existentes = self.tasks.obter_tarefas()
        titulos_existentes = [t["titulo"] for t in tarefas_existentes]
        
        for item in produtos:
            if len(item) == 3:
                codigo, nome, qtd = item
            else:
                produto, qtd, custo = item
                nome = produto
                codigo = None
            
            try:
                qtd = int(qtd)
            except:
                qtd = 0
            
            if qtd < 5 and qtd > 0:
                if codigo:
                    titulo_tarefa = f"Reabastecer {nome} (código {codigo})"
                else:
                    titulo_tarefa = f"Reabastecer {nome}"
                
                if titulo_tarefa not in titulos_existentes:
                    self.tasks.criar_tarefa(titulo_tarefa, "compra", prioridade=3)
                    self.tasks.registrar_observacao(f"Estoque baixo: {nome} tem {qtd} unidades", "alerta")
                    self.event_bus.emitir("estoque_baixo", {"produto": nome, "estoque": qtd})
        
        # Verifica lucro (com tratamento de erro)
        try:
            compras, vendas = db.obter_resumo()
            lucro = vendas - compras
        except:
            compras = 0
            vendas = 0
            lucro = 0
        
        if lucro < 0:
            obs_recentes = self.tasks.obter_observacoes_nao_lidas()
            ja_tem_lucro = any("Lucro negativo" in o["mensagem"] for o in obs_recentes)
            
            if not ja_tem_lucro:
                self.tasks.registrar_observacao(f"Lucro negativo: R$ {lucro:.2f}", "alerta")
                
                if "Revisar precos" not in titulos_existentes:
                    self.tasks.criar_tarefa("Revisar precos", "analise", prioridade=5)
        
    def _saudacao(self):
        agora = datetime.now()
        if 5 <= agora.hour < 12:
            periodo = "manhã"
        elif 12 <= agora.hour < 18:
            periodo = "tarde"
        else:
            periodo = "noite"
        
        tarefas = self.tasks.obter_tarefas()
        if tarefas:
            pendentes = f" Voce tem {len(tarefas)} tarefa(s) pendente(s)."
        else:
            pendentes = ""
        
        return f"Bom {periodo}! Sao {agora.hour}:{agora.minute:02d}.{pendentes}"
    
    def processar(self, msg):
        msg_lower = msg.lower().strip()
        
        # Saudação (prioridade máxima)
        if msg_lower in ["oi", "ola", "olá", "bom dia", "boa tarde", "boa noite"]:
            return self._saudacao()
        
        # Despedida
        if msg_lower in ["tchau", "sair", "fim", "desligar", "encerrar"]:
            return "Até logo!"
        
        # VERIFICA AGENTES PRIMEIRO (antes do contexto/NLP)
        for nome, agente in self.agentes.items():
            if agente.pode_processar(msg):
                resposta = agente.processar(msg)
                self.contexto.registrar(msg, resposta, {"intencao": nome, "entidades": {}})
                return resposta
        
        # Se nenhum agente pegou, usa o contexto/NLP
        analise = self.contexto.analisar(msg)
        intencao = analise["intencao"]
        
        # Tarefas
        if intencao == "tarefas":
            tarefas = self.tasks.obter_tarefas()
            if tarefas:
                resposta = "📋 Tarefas pendentes:\n"
                for t in tarefas:
                    resposta += f"  • {t['titulo']} (prioridade {t['prioridade']})\n"
            else:
                resposta = "📋 Nenhuma tarefa pendente"
            
            obs = self.tasks.obter_observacoes_nao_lidas()
            for o in obs:
                resposta += f"\n📢 {o['mensagem']}"
                self.tasks.marcar_como_lida(o['id'])
            
            self.contexto.registrar(msg, resposta, analise)
            return resposta
        
        # Não entendeu
        if intencao == "desconhecido":
            resposta = "Não entendi. Diga: comprei, vendi, estoque, resumo, atualizar, ou use códigos como 'vende 2 do 720'"
            self.contexto.registrar(msg, resposta, analise)
            return resposta
        
        # Chama o agente pela intenção (fallback)
        if intencao in self.agentes:
            agente = self.agentes[intencao]
            resposta = agente.processar(msg)
            self.contexto.registrar(msg, resposta, analise)
            
            if intencao in ["compra", "venda"]:
                self._verificar_rotina()
            
            return resposta
        
        return "Erro: agente não encontrado"