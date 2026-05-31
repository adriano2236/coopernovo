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
        self.ultimo_produto = None
        self.arquivo_contexto = "contexto.json"
        self._carregar_contexto()
    
    def _carregar_contexto(self):
        if os.path.exists(self.arquivo_contexto):
            with open(self.arquivo_contexto, 'r') as f:
                dados = json.load(f)
                self.historico = dados.get("historico", [])
                self.ultimo_produto = dados.get("ultimo_produto", None)
    
    def _salvar_contexto(self):
        with open(self.arquivo_contexto, 'w') as f:
            json.dump({
                "historico": self.historico[-50:],
                "ultimo_produto": self.ultimo_produto
            }, f, indent=2)
    
    def analisar(self, mensagem):
        """Analisa mensagem e retorna intenção + entidades"""
        intencao = self.intent_classifier.classificar(mensagem)
        entidades = self.entity_extractor.extrair_tudo(mensagem)
        
        # Se for referência a "esse" ou "mais", usa último produto
        if intencao in ["compra", "venda"]:
            if entidades["produto"] == "produto" or entidades["produto"] in ["esse", "este", "isso"]:
                if self.ultimo_produto:
                    entidades["produto"] = self.ultimo_produto
                    entidades["referencia"] = True
        
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
        
        if analise["entidades"].get("produto"):
            self.ultimo_produto = analise["entidades"]["produto"]
        
        self._salvar_contexto()
    
    def obter_contexto(self, mensagem):
        analise = self.analisar(mensagem)
        return {
            "intencao": analise["intencao"],
            "entidades": analise["entidades"],
            "ultimo_produto": self.ultimo_produto
        }