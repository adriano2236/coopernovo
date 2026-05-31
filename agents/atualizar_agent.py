# agents/atualizar_agent.py
from agents.base_agent import BaseAgent
import re
from repositories.produto_repository import (
    buscar_produto,
    atualizar_nome,
    atualizar_preco,
    atualizar_estoque,
)

class AtualizarAgent(BaseAgent):
    def __init__(self):
        super().__init__("Atualizar")
    
    def pode_processar(self, msg):
        msg_lower = msg.lower()
        return "atualizar" in msg_lower or "alterar" in msg_lower
    
    def processar(self, msg):
        msg_lower = msg.lower()
        
        # ========== EXTRAÇÃO ==========
        # Extrai código
        codigo_match = re.search(r'(\d+)', msg)
        codigo = codigo_match.group(1) if codigo_match else None
        
        if not codigo:
            return "⚠️ Diga o código do produto. Ex: atualizar produto 720 preco_venda 29.90"
        
        produto = buscar_produto(codigo)
        if not produto:
            return f"⚠️ Produto com código {codigo} não encontrado. Cadastre primeiro com: comprei X produto codigo {codigo} por Y reais"
        
        # ========== ATUALIZAR NOME ==========
        if "nome" in msg_lower:
            # Regex melhorada para capturar o nome ignorando termos técnicos subsequentes
            nome_match = re.search(r'nome\s+(.+?)(?:\s+(?:codigo|preco|estoque|venda)|$)', msg_lower)
            if nome_match:
                novo_nome = nome_match.group(1).strip()
                if len(novo_nome) < 2:
                    return "⚠️ Nome muito curto. Use um nome descritivo."
                atualizar_nome(codigo, novo_nome)       
                return f"✅ Produto {codigo} agora se chama: {novo_nome}"
            return "Use: atualizar produto 720 nome calcinha renda preta"
        
        # ========== ATUALIZAR PREÇO (Unificando regex) ==========
        if any(x in msg_lower for x in ["preco", "valor", "preço"]):
            preco_match = re.search(r'(?:preco_venda|preco|valor)\s*(\d+(?:[.,]\d+)?)', msg_lower)
            if preco_match:
                preco = float(preco_match.group(1).replace(",", "."))
                
                if preco <= 0:
                    return "⚠️ Preço inválido. Use um valor maior que zero."
                
                atualizar_preco(codigo, preco)
                return f"✅ Produto {codigo} agora custa R$ {preco:.2f}"
            return "Use: atualizar produto 720 preco_venda 29.90"
        
        # ========== ATUALIZAR ESTOQUE ==========
        if "estoque" in msg_lower:
            estoque_match = re.search(r'estoque\s*(\d+)', msg_lower)
            if estoque_match:
                estoque = int(estoque_match.group(1))
                
                # ========== VALIDAÇÃO 4: Estoque não pode ser negativo ==========
                if estoque < 0:
                    return "⚠️ Estoque não pode ser negativo. Use um valor maior ou igual a zero."
                
                atualizar_estoque(codigo, estoque)
                return f"✅ Produto {codigo} agora tem {estoque} unidades"
            return "Use: atualizar produto 720 estoque 100"
        
        return "Use: atualizar produto 720 nome 'produto' ou preco_venda 29.90 ou estoque 100"