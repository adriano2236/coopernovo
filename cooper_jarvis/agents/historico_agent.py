"""Agente do historico de conversa."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agents.base_agent import BaseAgent
from repositories.historico_repository import HistoricoRepository


class HistoricoAgent(BaseAgent):
    """Gerencia a memoria de historico de conversa."""

    nome = "historico"
    limite_eventos = 100

    def __init__(self, repository: HistoricoRepository | None = None) -> None:
        self.repository = repository or HistoricoRepository()

    def pode_processar(self, analise: dict[str, Any]) -> bool:
        """Identifica consultas sobre o historico de conversa."""
        return analise.get("intencao") == "historico_consultar"

    def processar(self, analise: dict[str, Any]) -> dict[str, Any]:
        """Recupera o historico de conversa salvo."""
        eventos = self.recuperar_historico()
        return {
            "agent": self.nome,
            "tipo": "historico",
            "dados": {
                "mensagem": self._montar_resposta(eventos),
                "eventos": eventos,
            },
        }

    def registrar_interacao(
        self,
        analise: dict[str, Any],
        resultado: dict[str, Any],
        resposta: str,
    ) -> list[dict[str, Any]]:
        """Decide como transformar uma interacao em evento de historico."""
        eventos = self.repository.recuperar()
        eventos.append(
            {
                "timestamp": self._agora(),
                "comando": analise.get("texto_original") or "",
                "resposta": resposta,
                "agente": resultado.get("agent") or "",
            }
        )
        eventos = eventos[-self.limite_eventos :]
        return self.repository.salvar(eventos)

    def recuperar_historico(self) -> list[dict[str, Any]]:
        """Recupera os eventos do historico."""
        return self.repository.recuperar()

    def _montar_resposta(self, eventos: list[dict[str, Any]]) -> str:
        if not eventos:
            return "Ainda nao existe historico de conversa salvo."

        ultimos = eventos[-5:]
        linhas = ["Historico de conversa:"]
        for evento in ultimos:
            linhas.append(
                "- "
                f"{evento.get('timestamp') or 'sem data'} | "
                f"{evento.get('agente') or 'sem agente'} | "
                f"{evento.get('comando') or 'sem comando'}"
            )
        return "\n".join(linhas)

    def _agora(self) -> str:
        """Retorna timestamp atual em UTC."""
        return datetime.now(timezone.utc).isoformat()
