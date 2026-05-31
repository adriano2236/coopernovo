# tools/compra_tools.py
import sqlite3
from datetime import datetime

class CompraTools:
    def __init__(self):
        self.db_file = "loja.db"
    
    def registrar_compra(self, produto, quantidade, preco):
        """Registra uma compra no banco de dados"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        total = quantidade * preco
        data = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # Insere compra
        cursor.execute('''
            INSERT INTO compras (produto, quantidade, preco, total, data)
            VALUES (?, ?, ?, ?, ?)
        ''', (produto, quantidade, preco, total, data))
        
        # Atualiza estoque
        cursor.execute('''
            INSERT INTO produtos (nome, estoque, custo)
            VALUES (?, ?, ?)
            ON CONFLICT(nome) DO UPDATE SET
                estoque = estoque + ?,
                custo = ?
        ''', (produto, quantidade, preco, quantidade, preco))
        
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
    
    def obter_total_compras(self):
        """Retorna total de compras"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(total) FROM compras')
        total = cursor.fetchone()[0] or 0
        conn.close()
        return total