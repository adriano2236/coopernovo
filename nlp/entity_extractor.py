# nlp/entity_extractor.py
import re
from nlp.patterns import Patterns

class EntityExtractor:
    def __init__(self):
        self.patterns = Patterns()
    
    def extrair_quantidade(self, mensagem):
        msg = mensagem.lower()
        
        # "uma" ou "um" = 1
        if re.search(r'\buma\b|\bum\b', msg):
            return 1
        
        # Número comum
        for pattern in self.patterns.ENTITY_PATTERNS["quantidade"]:
            match = re.search(pattern, msg)
            if match:
                for grupo in match.groups():
                    if grupo and grupo.isdigit():
                        return int(grupo)
        return 0
    
    def extrair_preco(self, mensagem):
        for pattern in self.patterns.ENTITY_PATTERNS["preco"]:
            match = re.search(pattern, mensagem)
            if match:
                for grupo in match.groups():
                    if grupo:
                        valor = grupo.replace(",", ".")
                        try:
                            return float(valor)
                        except:
                            pass
        return 0.0
    
    def extrair_codigo(self, mensagem):
        """Extrai código do produto (ex: codigo 721, SKU:123, #456)"""
        msg = mensagem.lower()
        
        patterns = [
            r'codigo\s*(\d+)',
            r'código\s*(\d+)',
            r'sku[:]?\s*(\d+)',
            r'#(\d+)',
            r'produto\s*(\d+)',
            r'de\s*(\d+)',
            r'do\s*(\d+)',
            r'da\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, msg)
            if match:
                return match.group(1)
        
        return None
    
    def extrair_produto(self, mensagem):
        msg = mensagem.lower()
        
        palavras = msg.split()
        
        ignorar = {
            "comprei", "comprar", "vendi", "vender",
            "por", "reais", "real", "codigo", "código"
        }
        
        for i, palavra in enumerate(palavras):
           
            if palavra.isdigit() or palavra in ["um", "uma"]:
               
                produto = []
        
                for p in palavras[i + 1:]:
                   
                    if p in ignorar:
                        break
                     
                    if p.replace(".", "").replace(",", "").isdigit():
                        break
                     
                    produto.append(p)

                    if produto and produto[0] in ["de", "do", "da"]:
                        return "produto"
        
                if produto:
                    return " ".join(produto)
        
        return "produto"
    
    def extrair_tudo(self, mensagem):
        return {
            "quantidade": self.extrair_quantidade(mensagem),
            "preco": self.extrair_preco(mensagem),
            "codigo": self.extrair_codigo(mensagem),  # <-- NOVO
            "produto": self.extrair_produto(mensagem),
        }