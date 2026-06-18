"""Agente de tarefas e compromissos pessoais."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agents.base_agent import BaseAgent
from repositories.agenda_repository import AgendaRepository


class AgendaAgent(BaseAgent):
    """Gerencia tarefas pessoais do Cooper Jarvis."""

    nome = "agenda"

    def __init__(self, repository: AgendaRepository | None = None) -> None:
        self.repository = repository or AgendaRepository()

    def pode_processar(self, analise: dict[str, Any]) -> bool:
        """Identifica comandos de agenda."""
        return str(analise.get("intencao") or "").startswith("agenda_")

    def processar(self, analise: dict[str, Any]) -> dict[str, Any]:
        """Executa a acao de agenda solicitada."""
        intencao = analise.get("intencao")
        entidades = analise.get("entidades") or {}
        comando = analise.get("texto_original") or ""

        if intencao == "agenda_criar_tarefa":
            return self._criar_tarefa(comando, entidades)
        if intencao == "agenda_listar_tarefas":
            return self._listar_tarefas(comando)
        if intencao == "agenda_concluir_tarefa":
            return self._concluir_tarefa(comando, entidades)
        if intencao == "agenda_remover_tarefa":
            return self._remover_tarefa(comando, entidades)

        return self._resposta(
            mensagem="Ainda nao sei executar essa acao de agenda.",
            resultado="acao_nao_suportada",
        )

    def _criar_tarefa(
        self,
        comando: str,
        entidades: dict[str, Any],
    ) -> dict[str, Any]:
        descricao = str(entidades.get("descricao_tarefa") or "").strip()
        if not descricao:
            return self._finalizar(
                comando,
                "descricao_vazia",
                "Informe a descricao da tarefa.",
            )

        tarefas = self.repository.recuperar_tarefas()
        tarefa = {
            "id": self._proximo_id(tarefas),
            "descricao": descricao,
            "status": "pendente",
            "data_criacao": self._agora(),
            "data_conclusao": None,
        }
        tarefas.append(tarefa)
        self.repository.salvar_tarefas(tarefas)

        return self._finalizar(
            comando,
            "tarefa_criada",
            f"Tarefa criada: #{tarefa['id']} - {tarefa['descricao']}",
            tarefa,
        )

    def _listar_tarefas(self, comando: str) -> dict[str, Any]:
        tarefas = self.repository.recuperar_tarefas()
        if not tarefas:
            return self._finalizar(
                comando,
                "sem_tarefas",
                "Nenhuma tarefa cadastrada.",
            )

        linhas = ["Tarefas:"]
        for tarefa in tarefas:
            linhas.append(
                "- "
                f"#{tarefa.get('id')} | "
                f"{tarefa.get('status')} | "
                f"{tarefa.get('descricao')}"
            )

        return self._finalizar(
            comando,
            "tarefas_listadas",
            "\n".join(linhas),
            {"tarefas": tarefas},
        )

    def _concluir_tarefa(
        self,
        comando: str,
        entidades: dict[str, Any],
    ) -> dict[str, Any]:
        tarefas = self.repository.recuperar_tarefas()
        tarefa = self._encontrar_tarefa(tarefas, entidades)
        if tarefa is None:
            return self._finalizar(
                comando,
                "tarefa_nao_encontrada",
                "Nao encontrei essa tarefa para concluir.",
            )

        tarefa["status"] = "concluida"
        tarefa["data_conclusao"] = self._agora()
        self.repository.salvar_tarefas(tarefas)

        return self._finalizar(
            comando,
            "tarefa_concluida",
            f"Tarefa concluida: #{tarefa['id']} - {tarefa['descricao']}",
            tarefa,
        )

    def _remover_tarefa(
        self,
        comando: str,
        entidades: dict[str, Any],
    ) -> dict[str, Any]:
        tarefas = self.repository.recuperar_tarefas()
        tarefa = self._encontrar_tarefa(tarefas, entidades)
        if tarefa is None:
            return self._finalizar(
                comando,
                "tarefa_nao_encontrada",
                "Nao encontrei essa tarefa para remover.",
            )

        tarefas = [item for item in tarefas if item.get("id") != tarefa.get("id")]
        self.repository.salvar_tarefas(tarefas)

        return self._finalizar(
            comando,
            "tarefa_removida",
            f"Tarefa removida: #{tarefa['id']} - {tarefa['descricao']}",
            tarefa,
        )

    def _encontrar_tarefa(
        self,
        tarefas: list[dict[str, Any]],
        entidades: dict[str, Any],
    ) -> dict[str, Any] | None:
        tarefa_id = entidades.get("id_tarefa")
        if tarefa_id is not None:
            for tarefa in tarefas:
                if tarefa.get("id") == tarefa_id:
                    return tarefa

        descricao = str(entidades.get("descricao_tarefa") or "").strip().lower()
        if not descricao:
            return None

        for tarefa in tarefas:
            if str(tarefa.get("descricao") or "").strip().lower() == descricao:
                return tarefa

        for tarefa in tarefas:
            if descricao in str(tarefa.get("descricao") or "").strip().lower():
                return tarefa

        return None

    def _proximo_id(self, tarefas: list[dict[str, Any]]) -> int:
        ids = [int(tarefa.get("id") or 0) for tarefa in tarefas]
        return (max(ids) if ids else 0) + 1

    def _finalizar(
        self,
        comando: str,
        resultado: str,
        mensagem: str,
        dados_extras: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.repository.registrar_log(
            {
                "comando": comando,
                "resultado": resultado,
                "timestamp": self._agora(),
            }
        )
        return self._resposta(mensagem, resultado, dados_extras)

    def _resposta(
        self,
        mensagem: str,
        resultado: str,
        dados_extras: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        dados = {
            "mensagem": mensagem,
            "resultado": resultado,
        }
        if dados_extras:
            dados.update(dados_extras)

        return {
            "agent": self.nome,
            "tipo": "agenda",
            "dados": dados,
        }

    def _agora(self) -> str:
        """Retorna timestamp atual em UTC."""
        return datetime.now(timezone.utc).isoformat()
