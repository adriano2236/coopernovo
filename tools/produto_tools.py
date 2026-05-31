# tools/produto_tools.py
import sqlite3

class ProdutoTools:
    def __init__(self):
        self.db_file = "cooper.db"
    
    def buscar_por_codigo(self, codigo):
        """Busca produto pelo código (720, 721, etc)"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT codigo, nome, categoria, estoque, custo_medio, preco_venda
            FROM produtos 
            WHERE codigo = ?
        ''', (codigo,))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            return {
                "codigo": resultado[0],
                "nome": resultado[1],
                "categoria": resultado[2],
                "estoque": resultado[3],
                "custo_medio": resultado[4],
                "preco_venda": resultado[5]
            }
        return None
    
    def cadastrar_produto(self, codigo, nome, categoria, custo_medio, preco_venda, estoque=0):
        """Cadastra um novo produto"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO produtos (codigo, nome, categoria, estoque, custo_medio, preco_venda)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (codigo, nome, categoria, estoque, custo_medio, preco_venda))
        
        conn.commit()
        conn.close()
        return True
    
    def atualizar_estoque(self, codigo, quantidade):
        """Atualiza estoque (positivo = compra, negativo = venda)"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE produtos SET estoque = estoque + ? WHERE codigo = ?
        ''', (quantidade, codigo))
        
        conn.commit()
        conn.close()
        return True