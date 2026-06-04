# nlp/intent_classifier.py
from nlp.patterns import Patterns

class IntentClassifier:
    def __init__(self):
        self.patterns = Patterns()
    
    def classificar(self, mensagem):
        msg_lower = mensagem.lower().strip()
        
        pontuacoes = {}
        
        for intent, palavras in self.patterns.INTENTS.items():
            pontuacao = 0
            for palavra in palavras:
                if palavra in msg_lower:
                    pontuacao += 1
            if pontuacao > 0:
                pontuacoes[intent] = pontuacao
        
        if not pontuacoes:
            return "desconhecido"
        
        # Retorna a intenção com maior pontuação
        return max(pontuacoes, key=pontuacoes.get)