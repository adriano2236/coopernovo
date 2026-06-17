"""Formatador de respostas do Cooper Jarvis."""

from typing import Any


class ResponseBuilder:
    """Transforma dados internos em texto para o usuario."""

    def formatar(self, resultado: dict[str, Any]) -> str:
        """Formata uma resposta simples."""
        dados = resultado.get("dados") or {}
        return str(dados.get("mensagem") or "Operacao concluida.")
