import sqlite3

DB_FILE = "cooper.db"

def buscar_produto(codigo):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        'SELECT codigo, nome FROM produtos WHERE codigo = ?',
        (codigo,)
    )

    produto = cursor.fetchone()

    conn.close()

    return produto

def atualizar_nome(codigo, novo_nome):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        'UPDATE produtos SET nome = ? WHERE codigo = ?',
        (novo_nome, codigo)
    )

    conn.commit()
    conn.close()

def atualizar_preco(codigo, preco):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        'UPDATE produtos SET preco_venda = ? WHERE codigo = ?',
        (preco, codigo)
    )

    conn.commit()
    conn.close()

def atualizar_estoque(codigo, estoque):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        'UPDATE produtos SET estoque = ? WHERE codigo = ?',
        (estoque, codigo)
    )

    conn.commit()
    conn.close()