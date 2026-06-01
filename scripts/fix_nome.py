# fix_nome.py
import sqlite3

conn = sqlite3.connect('cooper.db')
cursor = conn.cursor()

cursor.execute("UPDATE produtos SET nome = 'calcinha renda preta' WHERE codigo = '720'")
conn.commit()

cursor.execute("SELECT codigo, nome, estoque FROM produtos")
print(cursor.fetchall())

conn.close()
print("✅ Nome atualizado!")