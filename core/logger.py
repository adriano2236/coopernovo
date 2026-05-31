# core/logger.py
import logging
import os

class CooperLogger:
    def __init__(self):
        os.makedirs("logs", exist_ok=True)
        self.logger = logging.getLogger("cooper")
        self.logger.setLevel(logging.DEBUG)
        
        fh = logging.FileHandler("logs/cooper.log", encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
    
    def info(self, msg):
        self.logger.info(msg)

    def advertência(self, msg):
        self.logger.warning(msg)
    
    def error(self, msg):
        self.logger.error(msg)
    
    def acao(self, tipo, detalhes):
        self.info(f"🛒 {tipo}: {detalhes}")

    def warning(self, msg):
        self.logger.warning(msg)