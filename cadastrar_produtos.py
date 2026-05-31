# agents/cadastro_agent.py
from agents.base_agent import BaseAgent
from tools.produto_tools import ProdutoTools
import re

class CadastroAgent(BaseAgent):
    def __init__(self):
        super().__init__("Cadastro")
        self.produto_tools = ProdutoTools()
    
    def pode_processar(self, msg):
        return "cadastrar" in msg.lower() or "novo produto" in msg.lower()
    
    def processar(self, msg):
        # Extrai código
        codigo_match = re.search(r'codigo\s*(\d+)', msg)
        codigo = codigo_match.group(1) if codigo_match else None
        
        # Extrai nome
        nome_match = re.search(r'nome\s*([a-zá-ú\s]+)', msg.lower())
        nome = nome_match.group(1).strip() if nome_match else None
        
        # Extrai categoria
        cat_match = re.search(r'categoria\s*([a-zá-ú]+)', msg.lower())
        categoria = cat_match.group(1) if cat_match else "geral"
        
        # Extrai custo
        custo_match = re.search(r'custo\s*(\d+(?:[.,]\d+)?)', msg)
        custo = float(custo_match.group(1).replace(",", ".")) if custo_match else 0
        
        # Extrai venda
        venda_match = re.search(r'venda\s*(\d+(?:[.,]\d+)?)', msg)
        venda = float(venda_match.group(1).replace(",", ".")) if venda_match else 0
        
        # Extrai estoque
        est_match = re.search(r'estoque\s*(\d+)', msg)
        estoque = int(est_match.group(1)) if est_match else 0
        
        if codigo and nome:
            self.produto_tools.cadastrar_produto(codigo, nome, categoria, custo, venda, estoque)
            return f"✅ Produto {nome} (código {codigo}) cadastrado com sucesso!"
        
        return "Use: cadastrar produto codigo 500 nome saia jeans categoria moda custo 25 venda 60 estoque 50"