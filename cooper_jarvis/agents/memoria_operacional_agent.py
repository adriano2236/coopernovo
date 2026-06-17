"""Agente da memoria operacional."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agents.base_agent import BaseAgent
from repositories.memoria_operacional_repository import MemoriaOperacionalRepository


class MemoriaOperacionalAgent(BaseAgent):
    """Gerencia fatos permanentes do Cooper Jarvis."""

    nome = "memoria_operacional"

    def __init__(
        self,
        repository: MemoriaOperacionalRepository | None = None,
    ) -> None:
        self.repository = repository or MemoriaOperacionalRepository()

    def pode_processar(self, analise: dict[str, Any]) -> bool:
        """Identifica registros e consultas da memoria operacional."""
        return analise.get("intencao") in {
            "memoria_operacional_registrar",
            "memoria_operacional_consultar",
        }

    def processar(self, analise: dict[str, Any]) -> dict[str, Any]:
        """Processa registro ou consulta de fatos permanentes."""
        if analise.get("intencao") == "memoria_operacional_registrar":
            return self._registrar(analise)

        return self._consultar(analise)

    def _registrar(self, analise: dict[str, Any]) -> dict[str, Any]:
        entidades = analise.get("entidades") or {}
        memoria = entidades.get("memoria_operacional") or {}
        if not memoria:
            return self._resposta(
                "Nao encontrei um fato operacional claro para guardar.",
                {},
            )

        memorias = self.repository.recuperar()
        memoria_salva = self._salvar_memoria(memorias, memoria)
        self.repository.salvar(memorias)

        return self._resposta(
            (
                "Memoria operacional salva.\n"
                f"- chave: {memoria_salva.get('chave')}\n"
                f"- categoria: {memoria_salva.get('categoria')}\n"
                f"- valor: {memoria_salva.get('valor')}"
            ),
            memoria_salva,
        )

    def _consultar(self, analise: dict[str, Any]) -> dict[str, Any]:
        entidades = analise.get("entidades") or {}
        chave = entidades.get("chave_memoria_operacional")
        categoria = entidades.get("categoria_memoria_operacional")
        memorias = self.repository.recuperar()

        if chave:
            memoria = self._buscar_por_chave(memorias, chave)
            return self._resposta(
                self._montar_resposta_chave(memoria, chave),
                {"memorias": [memoria] if memoria else []},
            )

        if categoria:
            memorias = [
                memoria
                for memoria in memorias
                if memoria.get("categoria") == categoria
            ]

        return self._resposta(
            self._montar_resposta_consulta(memorias, categoria),
            {"memorias": memorias},
        )

    def _buscar_por_chave(
        self,
        memorias: list[dict[str, Any]],
        chave: str,
    ) -> dict[str, Any] | None:
        for memoria in memorias:
            if memoria.get("chave") == chave:
                return memoria
        return None

    def _salvar_memoria(
        self,
        memorias: list[dict[str, Any]],
        nova_memoria: dict[str, str],
    ) -> dict[str, Any]:
        agora = self._agora()
        chave = nova_memoria.get("chave") or "geral"
        valor = nova_memoria.get("valor") or ""
        categoria = nova_memoria.get("categoria") or "geral"

        for memoria in memorias:
            if memoria.get("chave") == chave:
                memoria["valor"] = valor
                memoria["categoria"] = categoria
                memoria["data_atualizacao"] = agora
                return memoria

        memoria = {
            "chave": chave,
            "valor": valor,
            "categoria": categoria,
            "data_criacao": agora,
            "data_atualizacao": agora,
        }
        memorias.append(memoria)
        return memoria

    def _montar_resposta_consulta(
        self,
        memorias: list[dict[str, Any]],
        categoria: str | None,
    ) -> str:
        if not memorias:
            if categoria:
                return f"Ainda nao tenho memorias operacionais em {categoria}."
            return "Ainda nao tenho memorias operacionais salvas."

        linhas = ["Memoria operacional:"]
        for memoria in memorias:
            linhas.append(
                "- "
                f"{memoria.get('categoria') or 'geral'} | "
                f"{memoria.get('chave') or 'sem_chave'}: "
                f"{memoria.get('valor') or ''}"
            )
        return "\n".join(linhas)

    def _montar_resposta_chave(
        self,
        memoria: dict[str, Any] | None,
        chave: str,
    ) -> str:
        if not memoria:
            return f"Ainda nao tenho memoria operacional para {chave}."

        return str(memoria.get("valor") or "")

    def _resposta(
        self,
        mensagem: str,
        memoria: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "agent": self.nome,
            "tipo": "memoria_operacional",
            "dados": {
                "mensagem": mensagem,
                "memoria": memoria,
            },
        }

    def _agora(self) -> str:
        """Retorna timestamp atual em UTC."""
        return datetime.now(timezone.utc).isoformat()
