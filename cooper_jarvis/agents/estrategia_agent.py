"""Agente da memoria estrategica."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agents.base_agent import BaseAgent
from repositories.estrategia_repository import EstrategiaRepository


class EstrategiaAgent(BaseAgent):
    """Gerencia objetivos, projetos e metas do Cooper Jarvis."""

    nome = "estrategia"

    def __init__(self, repository: EstrategiaRepository | None = None) -> None:
        self.repository = repository or EstrategiaRepository()

    def pode_processar(self, analise: dict[str, Any]) -> bool:
        """Identifica registros e consultas estrategicas."""
        return analise.get("intencao") in {
            "estrategia_registrar",
            "estrategia_consultar",
        }

    def processar(self, analise: dict[str, Any]) -> dict[str, Any]:
        """Processa registro ou consulta de estrategia."""
        if analise.get("intencao") == "estrategia_registrar":
            return self._registrar(analise)

        return self._consultar(analise)

    def _registrar(self, analise: dict[str, Any]) -> dict[str, Any]:
        entidades = analise.get("entidades") or {}
        objetivo = entidades.get("objetivo_estrategico") or {}
        if not objetivo:
            return self._resposta(
                "Nao encontrei um objetivo estrategico claro para salvar.",
                {},
            )

        registros = self.repository.recuperar()
        registro = self._salvar_objetivo(registros, objetivo)
        self.repository.salvar(registros)

        return self._resposta(
            (
                "Objetivo estrategico salvo.\n"
                f"- objetivo: {registro.get('objetivo')}\n"
                f"- prioridade: {registro.get('prioridade')}\n"
                f"- status: {registro.get('status')}"
            ),
            registro,
        )

    def _consultar(self, analise: dict[str, Any]) -> dict[str, Any]:
        registros = self.repository.recuperar()
        return self._resposta(
            self._montar_resposta_consulta(registros),
            {"registros": registros},
        )

    def _salvar_objetivo(
        self,
        registros: list[dict[str, Any]],
        objetivo: dict[str, str],
    ) -> dict[str, Any]:
        agora = self._agora()
        nome_objetivo = objetivo.get("objetivo") or ""
        chave_objetivo = nome_objetivo.strip().lower()

        for registro in registros:
            if str(registro.get("objetivo") or "").strip().lower() == chave_objetivo:
                registro["descricao"] = objetivo.get("descricao") or nome_objetivo
                registro["prioridade"] = objetivo.get("prioridade") or "media"
                registro["status"] = objetivo.get("status") or registro.get("status") or "ativo"
                registro["data_atualizacao"] = agora
                return registro

        registro = {
            "objetivo": nome_objetivo,
            "descricao": objetivo.get("descricao") or nome_objetivo,
            "prioridade": objetivo.get("prioridade") or "media",
            "status": objetivo.get("status") or "ativo",
            "data_criacao": agora,
            "data_atualizacao": agora,
        }
        registros.append(registro)
        return registro

    def _montar_resposta_consulta(self, registros: list[dict[str, Any]]) -> str:
        if not registros:
            return "Ainda nao tenho objetivos estrategicos salvos."

        linhas = ["Objetivos estrategicos:"]
        for registro in registros:
            linhas.append(
                "- "
                f"{registro.get('objetivo') or 'sem objetivo'} | "
                f"prioridade {registro.get('prioridade') or 'media'} | "
                f"status {registro.get('status') or 'ativo'}"
            )
        return "\n".join(linhas)

    def _resposta(
        self,
        mensagem: str,
        estrategia: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "agent": self.nome,
            "tipo": "estrategia",
            "dados": {
                "mensagem": mensagem,
                "estrategia": estrategia,
            },
        }

    def _agora(self) -> str:
        """Retorna timestamp atual em UTC."""
        return datetime.now(timezone.utc).isoformat()
