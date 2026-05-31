# tools/venda_tools.py
import sqlite3
from datetime import datetime

class VendaTools:
    def __init__(self):
        self.db_file = "loja.db"
    
    def registrar_venda(self, produto, quantidade, preco):
        """Registra uma venda no banco de dados"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        total = quantidade * preco
        data = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # Verifica estoque
        cursor.execute('SELECT estoque FROM produtos WHERE nome = ?', (produto,))
        row = cursor.fetchone()
        
        if not row or row[0] < quantidade:
            conn.close()
            return {"erro": "estoque_insuficiente", "estoque": row[0] if row else 0}
        
        # Insere venda
        cursor.execute('''
            INSERT INTO vendas (produto, quantidade, preco, total, data)
            VALUES (?, ?, ?, ?, ?)
        ''', (produto, quantidade, preco, total, data))
        
        # Atualiza estoque
        cursor.execute('''
            UPDATE produtos SET estoque = estoque - ? WHERE nome = ?
        ''', (quantidade, produto))
        
        conn.commit()
        conn.close()
        
        return {
            "sucesso": True,
            "produto": produto,
            "quantidade": quantidade,
            "preco": preco,
            "total": total,
            "data": data
        }
    
    def obter_vendas_hoje(self):
        """Retorna vendas do dia"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        hoje = datetime.now().strftime("%d/%m/%Y")
        
        cursor.execute('''
            SELECT produto, quantidade, preco, total FROM vendas 
            WHERE data LIKE ?
        ''', (f"{hoje}%",))
        
        resultados = cursor.fetchall()
        conn.close()
        
        return [{"produto": r[0], "quantidade": r[1], "preco": r[2], "total": r[3]} for r in resultados]
    
    def obter_total_vendas(self):
        """Retorna total de vendas"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(total) FROM vendas')
        total = cursor.fetchone()[0] or 0
        conn.close()
        return total