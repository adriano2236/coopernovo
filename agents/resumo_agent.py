# agents/resumo_agent.py
from agents.base_agent import BaseAgent
import sqlite3

class ResumoAgent(BaseAgent):
    def __init__(self):
        super().__init__("Resumo")
        self.db_file = "cooper.db"
    
    def pode_processar(self, msg):
        return any(p in msg.lower() for p in ["lucro", "resumo", "total"])
    
    def processar(self, msg):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Total de compras
        cursor.execute('SELECT SUM(total) FROM compras')
        total_compras = cursor.fetchone()[0] or 0
        
        # Total de vendas
        cursor.execute('SELECT SUM(total) FROM vendas')
        total_vendas = cursor.fetchone()[0] or 0
        
        # Quantidade de produtos
        cursor.execute('SELECT COUNT(*) FROM produtos')
        qtd_produtos = cursor.fetchone()[0] or 0
        
        conn.close()
        
        lucro = total_vendas - total_compras
        lucro_str = f"R$ {lucro:.2f}"
        status = "💰 PREJUÍZO" if lucro < 0 else "✅ LUCRO"
        
        return f"""📊 RESUMO DO NEGÓCIO:
{"="*40}
💰 Total em Compras: R$ {total_compras:.2f}
💵 Total em Vendas:   R$ {total_vendas:.2f}
{"-"*40}
{status}: {lucro_str}
{"="*40}
📦 Produtos cadastrados: {qtd_produtos}"""