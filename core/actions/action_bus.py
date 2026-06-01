class ActionBus:
    def __init__(self):
        self.actions = {}

    def registrar(self, nome, funcao):
        self.actions[nome] = funcao

    def executar(self, nome, *args, **kwargs):
        if nome not in self.actions:
            return f"Ação '{nome}' não encontrada"
        
        try:
            return self.actions[nome](*args, **kwargs)
        except Exception as e:
            return f"Erro ao executar ação: {str(e)}"