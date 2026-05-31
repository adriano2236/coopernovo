# agents/vendas_agent.py
from agents.base_agent import BaseAgent
import re
import sqlite3
from datetime import datetime

class VendasAgent(BaseAgent):
    def __init__(self, event_bus=None):
        super().__init__("Vendas")
        self.event_bus = event_bus
        self.db_file = "cooper.db"
    
    def pode_processar(self, msg):
        return any(p in msg.lower() for p in ["vende", "vendi", "vender"])
    
    def processar(self, msg):
        msg_lower = msg.lower()
        
        # ========== EXTRAÇÃO ==========
        # Extrai quantidade
        qtd = 1
        
        qtd_match = re.search(
            r'(vendi|vende|vender)\s+(\d+)',
            msg_lower
        )
        
        if qtd_match:
            qtd = int(qtd_match.group(2))
        
        # Extrai código
        codigo = None
        patterns = [
            r'do\s*(\d+)', r'da\s*(\d+)', r'codigo\s*(\d+)',
            r'código\s*(\d+)', r'#(\d+)', r'\b(\d{3})\b'
        ]
        for pattern in patterns:
            match = re.search(pattern, msg_lower)
            if match:
                codigo = match.group(1)
                break
        
        # ========== VALIDAÇÕES ==========
        # VALIDAÇÃO 1: Quantidade deve ser positiva
        if qtd <= 0:
            return "⚠️ Quantidade inválida. Use um número maior que zero. Ex: vende 2 do 720"
        
        # VALIDAÇÃO 2: Código é obrigatório
        if not codigo:
            return "⚠️ Diga o código do produto. Ex: vende 2 do 720"
        
        # ========== BUSCA PRODUTO ==========
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT codigo, nome, estoque, preco_venda 
            FROM produtos WHERE codigo = ?
        ''', (codigo,))
        produto = cursor.fetchone()
        
        # VALIDAÇÃO 3: Produto existe
        if not produto:
            conn.close()
            return f"⚠️ Produto com código {codigo} não encontrado. Cadastre primeiro com: comprei X produto codigo {codigo} por Y reais"
        
        codigo_prod, nome_prod, estoque_prod, preco_prod = produto
        
        # VALIDAÇÃO 4: Preço de venda deve estar definido
        if not preco_prod or preco_prod <= 0:
            conn.close()
            return f"⚠️ Produto {nome_prod} (código {codigo}) não tem preço de venda definido. Use: atualizar produto {codigo} preco_venda 29.90"
        
        # VALIDAÇÃO 5: Estoque suficiente
        if estoque_prod < qtd:
            conn.close()
            return f"⚠️ Estoque insuficiente! Só tem {estoque_prod} {nome_prod} (código {codigo})"
        
        # ========== REGISTRA VENDA ==========
        total = qtd * preco_prod
        data = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO vendas (codigo, produto, quantidade, preco, total, data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (codigo, nome_prod, qtd, preco_prod, total, data))
        
        cursor.execute('UPDATE produtos SET estoque = estoque - ? WHERE codigo = ?', (qtd, codigo))
        conn.commit()
        conn.close()
        
        # ========== EVENTO ==========
        if self.event_bus:
            self.event_bus.emitir("venda_realizada", {
                "codigo": codigo,
                "produto": nome_prod,
                "quantidade": qtd,
                "preco": preco_prod,
                "total": total
            })
        
        return f"✅ Vendi {qtd} {nome_prod} (código {codigo}) por R$ {preco_prod:.2f} cada. Total: R$ {total:.2f}"