# database/db.py
import sqlite3
from datetime import datetime

class Database:
    def __init__(self):
        self.db_file = "cooper.db"
        self._criar_tabelas()
    
    def _criar_tabelas(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Tabela de produtos (COM CÓDIGO)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE,
                nome TEXT,
                categoria TEXT,
                estoque INTEGER DEFAULT 0,
                custo_medio REAL DEFAULT 0,
                preco_venda REAL DEFAULT 0
            )
        ''')
        
        # Tabela de compras
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT,
                produto TEXT,
                quantidade INTEGER,
                preco REAL,
                total REAL,
                data TEXT
            )
        ''')
        
        # Tabela de vendas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT,
                produto TEXT,
                quantidade INTEGER,
                preco REAL,
                total REAL,
                data TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados criado/verificado")
    
    def registrar_compra(self, codigo, quantidade, preco):
        """Registra compra (compatibilidade com código antigo)"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        total = quantidade * preco
        data = datetime.now().isoformat()
        
        # Insere compra
        cursor.execute('''
            INSERT INTO compras (codigo, quantidade, preco, total, data)
            VALUES (?, ?, ?, ?, ?)
        ''', (codigo, quantidade, preco, total, data))
        
        # Verifica se produto já existe (busca por código)
        cursor.execute('SELECT id, estoque FROM produtos WHERE codigo = ?', (codigo,))
        existe = cursor.fetchone()
        
        if existe:
            cursor.execute(
                'UPDATE produtos SET estoque = estoque + ? WHERE codigo = ?',
                (quantidade, codigo)
            )
        else:
            conn.close()
            return None

        conn.commit()
        conn.close()

        return total
    
    def registrar_venda(self, codigo, quantidade, preco):
        """Registra venda (compatibilidade com código antigo)"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        total = quantidade * preco
        data = datetime.now().isoformat()
        
        cursor.execute('SELECT estoque FROM produtos WHERE codigo = ?', (codigo,))
        row = cursor.fetchone()
        
        if not row or row[0] < quantidade:
            conn.close()
            return None
        
        cursor.execute('''
            INSERT INTO vendas (codigo, quantidade, preco, total, data)
            VALUES (?, ?, ?, ?, ?)
        ''', (codigo, quantidade, preco, total, data))
        
        cursor.execute('UPDATE produtos SET estoque = estoque - ? WHERE codigo = ?', (quantidade, codigo))
        
        conn.commit()
        conn.close()
        return total
    
    def obter_estoque(self):
        """Retorna lista de produtos (codigo, nome, estoque)"""
    
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        cursor.execute('''
            SELECT codigo, nome, estoque
            FROM produtos
            ORDER BY codigo
        ''')
    
        resultados = cursor.fetchall()
    
        conn.close()
    
        return resultados
    
    def obter_resumo(self):
        """Retorna total de compras e vendas"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT SUM(total) FROM compras')
        total_compras = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT SUM(total) FROM vendas')
        total_vendas = cursor.fetchone()[0] or 0
        
        conn.close()
        return total_compras, total_vendas
    
    # ========== NOVOS MÉTODOS PARA CÓDIGOS ==========
    
    def buscar_produto_por_codigo(self, codigo):
        """Busca produto pelo código"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT codigo, nome, categoria, estoque, custo_medio, preco_venda
            FROM produtos WHERE codigo = ?
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
        """Cadastra um novo produto com código"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO produtos (codigo, nome, categoria, estoque, custo_medio, preco_venda)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (codigo, nome, categoria, estoque, custo_medio, preco_venda))
        
        conn.commit()
        conn.close()
        return True
    
    def atualizar_estoque_por_codigo(self, codigo, quantidade):
        """Atualiza estoque usando código"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('UPDATE produtos SET estoque = estoque + ? WHERE codigo = ?', (quantidade, codigo))
        conn.commit()
        conn.close()
        return True
    
    def atualizar_nome_por_codigo(self, codigo, novo_nome):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute(
            'UPDATE produtos SET nome = ? WHERE codigo = ?',
            (novo_nome, codigo)
        )

        conn.commit()
        conn.close()
        return True
    
    def atualizar_preco_por_codigo(self, codigo, preco):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        cursor.execute(
            'UPDATE produtos SET preco_venda = ? WHERE codigo = ?',
            (preco, codigo)
        )
    
        conn.commit()
        conn.close()
        return True