# agents/compras_agent.py
from agents.base_agent import BaseAgent
import re
import sqlite3
from datetime import datetime

class ComprasAgent(BaseAgent):
    def __init__(self, event_bus=None):
        super().__init__("Compras")
        self.event_bus = event_bus
        self.db_file = "cooper.db"
    
    def pode_processar(self, msg):
        return "comprei" in msg.lower()
    
    def processar(self, msg):
        msg_lower = msg.lower()
        
        # ========== EXTRAÇÃO ==========
        # Extrai quantidade
        qtd_match = re.search(r'(\d+)', msg)
        qtd = int(qtd_match.group(1)) if qtd_match else 0
        
        # Extrai preço
        preco_match = re.search(r'por\s*(\d+(?:[.,]\d+)?)', msg)
        preco = float(preco_match.group(1).replace(",", ".")) if preco_match else 0
        
        # Extrai código
        codigo_match = re.search(r'codigo\s*(\d+)', msg_lower)
        codigo = codigo_match.group(1) if codigo_match else None
        
        # Extrai nome do produto
        produto = "produto"
        
        if codigo:
            match = re.search(
                rf'comprei\s+\d+\s+(.+?)\s+codigo\s+{codigo}',
                msg_lower
            )
        
            if match:
                produto = match.group(1).strip()
        
        # ========== VALIDAÇÕES ==========
        # VALIDAÇÃO 1: Quantidade deve ser positiva
        if qtd <= 0:
            return "⚠️ Quantidade inválida. Use um número maior que zero. Ex: comprei 5 calcinha codigo 720 por 10 reais"
        
        # VALIDAÇÃO 2: Preço deve ser positivo
        if preco <= 0:
            return "⚠️ Preço inválido. Use um valor maior que zero. Ex: comprei 5 calcinha codigo 720 por 10 reais"
        
        # VALIDAÇÃO 3: Código é obrigatório
        if not codigo:
            return "⚠️ Diga o código do produto. Ex: comprei 5 calcinha codigo 720 por 10 reais"
        
        # ========== REGISTRA COMPRA ==========
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        total = qtd * preco
        data = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO compras (codigo, produto, quantidade, preco, total, data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (codigo, produto, qtd, preco, total, data))
        
        # Verifica se produto já existe
        cursor.execute('SELECT id, estoque, nome FROM produtos WHERE codigo = ?', (codigo,))
        existe = cursor.fetchone()
        
        if existe:
            cursor.execute('UPDATE produtos SET estoque = estoque + ?, custo_medio = ? WHERE codigo = ?', 
                          (qtd, preco, codigo))
        else:
            cursor.execute('''
                INSERT INTO produtos (codigo, nome, estoque, custo_medio)
                VALUES (?, ?, ?, ?)
            ''', (codigo, produto, qtd, preco))
        
        conn.commit()
        conn.close()
        
        # ========== EVENTO ==========
        if self.event_bus:
            self.event_bus.emitir("compra_realizada", {
                "codigo": codigo,
                "produto": produto,
                "quantidade": qtd,
                "preco": preco,
                "total": total
            })
        
        return f"✅ Comprei {qtd} {produto} (código {codigo}) por R$ {preco:.2f} cada. Total: R$ {total:.2f}"