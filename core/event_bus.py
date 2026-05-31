# core/event_bus.py
from datetime import datetime

class EventBus:
    def __init__(self):
        self.listeners = {}
    
    def registrar(self, evento, ouvinte):
        if evento not in self.listeners:
            self.listeners[evento] = []
        self.listeners[evento].append(ouvinte)
    
    def emitir(self, evento, dados=None):
        if evento in self.listeners:
            for ouvinte in self.listeners[evento]:
                ouvinte(evento, dados)