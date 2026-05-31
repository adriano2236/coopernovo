# agents/base_agent.py
class BaseAgent:
    """Classe base para todos os agentes do Cooper"""
    
    def __init__(self, nome):
        self.nome = nome
    
    def pode_processar(self, comando: str) -> bool:
        """Verifica se este agente pode processar o comando"""
        return False
    
    def processar(self, comando: str) -> str:
        """Processa o comando e retorna a resposta"""
        return f"Agente {self.nome} não implementado"
    
    def get_nome(self) -> str:
        """Retorna o nome do agente"""
        return self.nome