"""Interpretador inicial do Cooper Jarvis."""

from typing import Any


class Interpretador:
    """Transforma texto bruto em uma analise simples."""

    def interpretar(self, texto: str) -> dict[str, Any]:
        """Interpreta texto sem executar nenhuma acao."""
        texto_limpo = str(texto or "").strip()
        return {
            "texto_original": texto,
            "texto_normalizado": texto_limpo.lower(),
            "intencao": "conversa",
            "entidades": {},
        }
