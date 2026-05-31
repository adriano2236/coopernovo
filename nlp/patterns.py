# nlp/patterns.py

class Patterns:
    # Intenções e suas palavras-chave
    INTENTS = {
        "compra": ["comprei", "comprar", "adquiri", "adicionei"],
        "venda": ["vendi", "vender", "vendido", "vendeu"],
        "estoque": ["estoque", "quantos", "tem", "sobra", "resta", "saldo"],
        "resumo": ["lucro", "resumo", "total", "faturamento", "balanço"],
        "saudacao": ["oi", "ola", "bom dia", "boa tarde", "boa noite", "eai"],
        "despedida": ["tchau", "sair", "fim", "ate logo", "encerrar", "parar"],
        "tarefas": ["tarefas", "pendentes", "o que preciso fazer", "lista", "to do", "tarefa"],
    }
    
    # Padrões para extração de entidades (regex)
    ENTITY_PATTERNS = {
        "quantidade": [
            r'(\d+)\s*(?:unidades?|pecas?|itens?)?',
            r'uma\s+(\w+)|um\s+(\w+)',
        ],
        "preco": [
            r'por\s*R?\$?\s*(\d+(?:[.,]\d+)?)',
            r'(\d+(?:[.,]\d+)?)\s*reais?',
            r'R\$\s*(\d+(?:[.,]\d+)?)',
        ],
        "produto": [
            r'\d+\s+([a-zá-ú]+(?:s?))(?:\s+por)',
            r'uma\s+([a-zá-ú]+)|um\s+([a-zá-ú]+)',
        ]
    }
    
    # Pluralização simples
    @staticmethod
    def singular(palavra):
        if palavra.endswith("es"):
            return palavra[:-2]
        if palavra.endswith("s"):
            return palavra[:-1]
        return palavra
    
    