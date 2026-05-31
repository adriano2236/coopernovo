# core/tasks.py
from database.db import Database
from datetime import datetime
import sqlite3

class TaskManager:
    def __init__(self):
        self.db = Database()
    
    def criar_tarefa(self, titulo, tipo, prioridade=1):
        conn = sqlite3.connect(self.db.db_file)
        cursor = conn.cursor()
        
        # Cria tabela se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tarefas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT,
                tipo TEXT,
                prioridade INTEGER,
                status TEXT,
                criado_em TEXT
            )
        ''')
        
        cursor.execute('''
            INSERT INTO tarefas (titulo, tipo, prioridade, status, criado_em)
            VALUES (?, ?, ?, ?, ?)
        ''', (titulo, tipo, prioridade, 'pendente', datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return True
    
    def obter_tarefas(self):
        conn = sqlite3.connect(self.db.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tarefas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT,
                tipo TEXT,
                prioridade INTEGER,
                status TEXT,
                criado_em TEXT
            )
        ''')
        
        cursor.execute('''
            SELECT id, titulo, tipo, prioridade FROM tarefas
            WHERE status = 'pendente'
            ORDER BY prioridade DESC, criado_em ASC
        ''')
        
        resultados = cursor.fetchall()
        conn.close()
        
        return [{"id": r[0], "titulo": r[1], "tipo": r[2], "prioridade": r[3]} for r in resultados]
    
    def registrar_observacao(self, mensagem, tipo="insight"):
        conn = sqlite3.connect(self.db.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS observacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT,
                mensagem TEXT,
                data TEXT,
                lida INTEGER
            )
        ''')
        
        cursor.execute('''
            INSERT INTO observacoes (tipo, mensagem, data, lida)
            VALUES (?, ?, ?, 0)
        ''', (tipo, mensagem, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def obter_observacoes_nao_lidas(self):
        conn = sqlite3.connect(self.db.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS observacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT,
                mensagem TEXT,
                data TEXT,
                lida INTEGER
            )
        ''')
        
        cursor.execute('SELECT id, tipo, mensagem FROM observacoes WHERE lida = 0')
        resultados = cursor.fetchall()
        conn.close()
        
        return [{"id": r[0], "tipo": r[1], "mensagem": r[2]} for r in resultados]
    
    def marcar_como_lida(self, obs_id):
        conn = sqlite3.connect(self.db.db_file)
        cursor = conn.cursor()
        cursor.execute('UPDATE observacoes SET lida = 1 WHERE id = ?', (obs_id,))
        conn.commit()
        conn.close()