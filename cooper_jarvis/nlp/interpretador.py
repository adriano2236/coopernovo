"""Interpretador inicial do Cooper Jarvis."""

import unicodedata
from typing import Any


class Interpretador:
    """Transforma texto bruto em uma analise simples."""

    def interpretar(self, texto: str) -> dict[str, Any]:
        """Interpreta texto sem executar nenhuma acao."""
        texto_limpo = str(texto or "").strip()
        texto_normalizado = self._normalizar(texto_limpo)
        return {
            "texto_original": texto,
            "texto_normalizado": texto_normalizado,
            "intencao": self._identificar_intencao(texto_normalizado),
            "entidades": {},
        }

    def _identificar_intencao(self, texto: str) -> str:
        """Identifica apenas intencoes basicas sem executar acoes."""
        termos_contexto = {
            "contexto",
            "ultimo comando",
            "ultima resposta",
            "ultimo agente",
        }
        if any(termo in texto for termo in termos_contexto):
            return "contexto_consultar"

        return "conversa"

    def _normalizar(self, texto: str) -> str:
        """Normaliza texto para facilitar a interpretacao."""
        texto_normalizado = " ".join(texto.lower().split())
        texto_normalizado = unicodedata.normalize("NFD", texto_normalizado)
        return "".join(
            caractere
            for caractere in texto_normalizado
            if unicodedata.category(caractere) != "Mn"
        )
