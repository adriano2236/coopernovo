# agents/estoque_agent.py
from agents.base_agent import BaseAgent
import sqlite3

class EstoqueAgent(BaseAgent):
    def __init__(self):
        super().__init__("Estoque")
        self.db_file = "cooper.db"
    
    def pode_processar(self, msg: str) -> bool:
        """Só processa comandos relacionados a consulta de estoque"""
        return "estoque" in msg.lower()
    
    def processar(self, msg: str, analise=None) -> str:
        """Retorna a lista de produtos em estoque"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT codigo, nome, estoque, preco_venda 
            FROM produtos 
            WHERE estoque > 0
            ORDER BY codigo
        ''')
        
        produtos = cursor.fetchall()
        conn.close()
        
        if not produtos:
            return "📦 Nenhum produto cadastrado"
        
        # Formata a saída
        resultado = "\n📦 ESTOQUE:\n"
        resultado += "=" * 65 + "\n"
        resultado += f"{'CÓDIGO':<8} {'PRODUTO':<40} {'QTD':>6} {'PREÇO':>10}\n"
        resultado += "-" * 65 + "\n"
        
        for codigo, nome, estoque, preco in produtos:
            preco = preco if preco else 0
            resultado += f"{codigo:<8} {nome:<40} {estoque:>6}   R$ {preco:>7.2f}\n"
        
        resultado += "=" * 65
        
        return resultado