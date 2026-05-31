# tools/estoque_tools.py
from database.db import Database

class EstoqueTools:
    def __init__(self):
        self.db = Database()
    
    def obter_estoque(self):
        return self.db.obter_estoque()
    
    def verificar_estoque(self, produto, quantidade):
        produtos = self.db.obter_estoque()
        for p, qtd, custo in produtos:
            if p == produto:
                return {"tem": qtd >= quantidade, "estoque": qtd}
        return {"tem": False, "estoque": 0}
    
    def atualizar_estoque(self, produto, quantidade):
        # Estoque é atualizado via compra/venda, não diretamente
        return True