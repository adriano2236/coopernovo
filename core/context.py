# core/context.py
from nlp.intent_classifier import IntentClassifier
from nlp.entity_extractor import EntityExtractor
from datetime import datetime
import json
import os

class Contexto:
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()

        self.historico = []

        self.contexto = {
            "eventos": [],
            "estado_atual": {
                "ultimo_produto": {
                    "codigo": None,
                    "nome": None
                },
                "ultima_intencao": None
            }
        }

        self.arquivo_contexto = "contexto.json"
        self._carregar_contexto()
    
    def _carregar_contexto(self):
        if os.path.exists(self.arquivo_contexto):
            with open(self.arquivo_contexto, 'r') as f:
                dados = json.load(f)
                self.historico = dados.get("historico", [])
                self.contexto = dados.get("contexto", self.contexto)

    def _salvar_contexto(self):
        with open(self.arquivo_contexto, 'w') as f:
            json.dump({
                "historico": self.historico[-50:],
                "contexto": self.contexto
            }, f, indent=2)
    
    def analisar(self, mensagem):
        """Analisa mensagem e retorna intenção + entidades"""

        intencao = self.intent_classifier.classificar(mensagem)

        continuidade = ["mais", "repete", "repetir", "mesmo", "continua", "continuação"]

        entidades = self.entity_extractor.extrair_tudo(mensagem)

        produto = entidades.get("produto", "")

        # resolução de continuidade (NOVA LÓGICA)

        tokens = mensagem.lower().split()

        if any(palavra in tokens for palavra in continuidade):
            ultimo = self.contexto["estado_atual"]["ultimo_produto"]["codigo"]
            nome = self.contexto["estado_atual"]["ultimo_produto"]["nome"]
        
            if ultimo:
                entidades["codigo"] = ultimo
                entidades["produto"] = nome
                entidades["referencia"] = True

        # 🛡️ atualização de estado com validação anti-bug
        codigo = entidades.get("codigo")

        if codigo:
            self.contexto["estado_atual"]["ultimo_produto"] = {
                "codigo": codigo,
                "nome": entidades.get("produto")
            }

        # 🧠 atualiza intenção
        if intencao != "desconhecido":
            self.contexto["estado_atual"]["ultima_intencao"] = intencao
        
        self._salvar_contexto()

        return {
            "intencao": intencao,
            "entidades": entidades
        }
    
    
    def registrar(self, mensagem, resposta, analise):
        self.historico.append({
            "timestamp": datetime.now().isoformat(),
            "mensagem": mensagem,
            "resposta": resposta,
            "intencao": analise["intencao"]
        })

        if analise["intencao"] in ["compra", "venda"]:
            self.contexto["eventos"].append({
                "tipo": analise["intencao"],
                "produto": analise["entidades"].get("produto"),
                "quantidade": analise["entidades"].get("quantidade"),
                "timestamp": datetime.now().isoformat()
            })
        
        self._salvar_contexto()
    
    def obter_contexto(self, mensagem):
        analise = self.analisar(mensagem)
        return {
            "intencao": analise["intencao"],
            "entidades": analise["entidades"],
            "ultimo_produto": self.contexto["estado_atual"]["ultimo_produto"]["codigo"]
        }