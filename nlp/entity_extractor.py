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
        ]
        
        for pattern in patterns:
            match = re.search(pattern, msg)
            if match:
                return match.group(1)
        
        return None
    
    def extrair_produto(self, mensagem):
        msg = mensagem.lower()
        
        # Tenta extrair pelo padrão
        for pattern in self.patterns.ENTITY_PATTERNS["produto"]:
            match = re.search(pattern, msg)
            if match:
                for grupo in match.groups():
                    if grupo and not grupo.isdigit():
                        return self.patterns.singular(grupo)
        
        # Fallback: palavra após quantidade
        palavras = msg.split()
        for i, p in enumerate(palavras):
            if p.isdigit() or p in ["uma", "um"]:
                if i + 1 < len(palavras):
                    produto = palavras[i + 1]
                    # Remove "por" se vier depois
                    if produto == "por" and i + 2 < len(palavras):
                        produto = palavras[i + 2]
                    return self.patterns.singular(produto)
        
        return "produto"
    
    def extrair_tudo(self, mensagem):
        return {
            "quantidade": self.extrair_quantidade(mensagem),
            "preco": self.extrair_preco(mensagem),
            "codigo": self.extrair_codigo(mensagem),  # <-- NOVO
            "produto": self.extrair_produto(mensagem),
        }