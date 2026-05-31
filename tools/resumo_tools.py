# tools/resumo_tools.py
from tools.compra_tools import CompraTools
from tools.venda_tools import VendaTools

class ResumoTools:
    def __init__(self):
        self.compras = CompraTools()
        self.vendas = VendaTools()
    
    def obter_resumo(self):
        total_compras = self.compras.obter_total_compras()
        total_vendas = self.vendas.obter_total_vendas()
        lucro = total_vendas - total_compras
        
        return {
            "compras": total_compras,
            "vendas": total_vendas,
            "lucro": lucro
        }