from flask import Flask, render_template, jsonify, request
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.utils
import json
import os
import sys

# Adiciona o diretório raiz ao path para permitir a importação do core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.cooper import Cooper
    cooper_instancia = Cooper()
except ImportError:
    cooper_instancia = None

app = Flask(__name__)

# Caminho dinâmico para o banco de dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "cooper.db")

print(f"📁 Banco: {DB_PATH}")
print(f"✅ Arquivo existe: {os.path.exists(DB_PATH)}")

def get_produtos():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Busca apenas produtos com estoque positivo
        cursor.execute("SELECT codigo, nome, estoque, preco_venda FROM produtos WHERE estoque > 0 ORDER BY codigo")
        produtos = cursor.fetchall()
    
    return [
        {"codigo": p[0], "nome": p[1], "estoque": p[2], "preco_venda": p[3] or 0} 
        for p in produtos
    ]

def get_resumo():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(total), 0) FROM compras")
        total_compras = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(total), 0) FROM vendas")
        total_vendas = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM produtos WHERE estoque > 0")
        qtd_produtos = cursor.fetchone()[0]

    return {
        "total_compras": round(float(total_compras), 2),
        "total_vendas": round(float(total_vendas), 2),
        "lucro": round(float(total_vendas - total_compras), 2),
        "qtd_produtos": qtd_produtos
    }

def get_ultimas_vendas():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT codigo, produto, quantidade, total, data FROM vendas ORDER BY data DESC LIMIT 10")
        vendas = cursor.fetchall()
    return [
        {"codigo": v[0], "produto": v[1], "quantidade": v[2], "total": float(v[3]), "data": v[4]} 
        for v in vendas
    ]

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/produtos')
def api_produtos():
    result = get_produtos()
    print(f"📊 API /api/produtos retornou {len(result)} produtos")
    return jsonify(result)

@app.route('/api/resumo')
def api_resumo():
    return jsonify(get_resumo())

@app.route('/api/ultimas_vendas')
def api_ultimas_vendas():
    return jsonify(get_ultimas_vendas())

@app.route('/api/estoque_grafico')
def api_estoque_grafico():
    produtos = get_produtos()
    if not produtos:
        fig = px.bar(title='Nenhum produto cadastrado')
    else:
        df = pd.DataFrame(produtos)
        fig = px.bar(df, x='codigo', y='estoque', title='Estoque por Produto',
                     text='estoque', color='estoque',
                     labels={'codigo': 'Código', 'estoque': 'Quantidade'})
        fig.update_traces(textposition='outside')
        fig.update_layout(template='plotly_dark', height=400)
    return jsonify(json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)))

@app.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        if not cooper_instancia:
            return jsonify({'resposta': 'Erro: Módulo de inteligência não carregado.'})
            
        data = request.get_json()
        mensagem = data.get('mensagem', '')
        if not mensagem:
            return jsonify({'resposta': 'Digite algo...'})
        resposta = cooper_instancia.processar(mensagem)
        return jsonify({'resposta': resposta})
    except Exception as e:
        return jsonify({'resposta': f'Erro: {str(e)}'})

if __name__ == '__main__':
    print("🚀 Cooper Dashboard iniciado!")
    app.run(host='0.0.0.0', port=5000, debug=True)