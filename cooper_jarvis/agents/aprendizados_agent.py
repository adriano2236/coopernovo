"""Agente da memoria de aprendizados."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agents.base_agent import BaseAgent
from repositories.aprendizados_repository import AprendizadosRepository


class AprendizadosAgent(BaseAgent):
    """Identifica e registra padroes aprendidos com o uso."""

    nome = "aprendizados"

    def __init__(self, repository: AprendizadosRepository | None = None) -> None:
        self.repository = repository or AprendizadosRepository()

    def pode_processar(self, analise: dict[str, Any]) -> bool:
        """Identifica consultas sobre aprendizados."""
        return analise.get("intencao") == "aprendizados_consultar"

    def processar(self, analise: dict[str, Any]) -> dict[str, Any]:
        """Lista aprendizados ja identificados."""
        aprendizados = self.repository.recuperar()
        return {
            "agent": self.nome,
            "tipo": "aprendizados",
            "dados": {
                "mensagem": self._montar_resposta(aprendizados),
                "aprendizados": aprendizados,
            },
        }

    def registrar_interacao(
        self,
        analise: dict[str, Any],
        resultado: dict[str, Any],
        resposta: str,
    ) -> list[dict[str, Any]]:
        """Identifica padroes na interacao e registra aprendizados."""
        candidatos = self._identificar_padroes(analise, resultado)
        if not candidatos:
            return self.repository.recuperar()

        aprendizados = self.repository.recuperar()
        for candidato in candidatos:
            self._confirmar_aprendizado(aprendizados, candidato)

        return self.repository.salvar(aprendizados)

    def _identificar_padroes(
        self,
        analise: dict[str, Any],
        resultado: dict[str, Any],
    ) -> list[dict[str, Any]]:
        texto = str(analise.get("texto_normalizado") or "")
        dados = resultado.get("dados") or {}
        memoria = dados.get("memoria") or {}
        candidatos: list[dict[str, Any]] = []

        if "vs code" in texto or memoria.get("chave") == "editor_principal":
            valor = str(memoria.get("valor") or "VS Code")
            if "vs code" in valor.lower() or "vs code" in texto:
                candidatos.append(
                    self._candidato(
                        descricao="Usuario utiliza VS Code frequentemente",
                        confianca=0.55,
                        origem="padrao_editor",
                    )
                )

        if "cooper" in texto and (
            "projeto" in texto or memoria.get("chave") == "projeto_principal"
        ):
            candidatos.append(
                self._candidato(
                    descricao="Usuario trabalha no projeto Cooper",
                    confianca=0.6,
                    origem="padrao_projeto",
                )
            )

        if "python" in texto and (
            "prefiro" in texto
            or "preferencia" in texto
            or "uso" in texto
            or "programo" in texto
            or "gosto" in texto
        ):
            candidatos.append(
                self._candidato(
                    descricao="Usuario prefere Python",
                    confianca=0.6,
                    origem="padrao_preferencia",
                )
            )

        return candidatos

    def _confirmar_aprendizado(
        self,
        aprendizados: list[dict[str, Any]],
        candidato: dict[str, Any],
    ) -> dict[str, Any]:
        agora = self._agora()
        descricao = candidato["descricao"]

        for aprendizado in aprendizados:
            if aprendizado.get("descricao") == descricao:
                aprendizado["confianca"] = min(
                    1.0,
                    round(
                        max(
                            float(aprendizado.get("confianca") or 0),
                            float(candidato.get("confianca") or 0),
                        )
                        + 0.1,
                        2,
                    ),
                )
                aprendizado["origem"] = candidato.get("origem") or "interacao"
                aprendizado["ultima_confirmacao"] = agora
                return aprendizado

        aprendizado = {
            "descricao": descricao,
            "confianca": candidato.get("confianca") or 0.5,
            "origem": candidato.get("origem") or "interacao",
            "data_criacao": agora,
            "ultima_confirmacao": agora,
        }
        aprendizados.append(aprendizado)
        return aprendizado

    def _candidato(
        self,
        descricao: str,
        confianca: float,
        origem: str,
    ) -> dict[str, Any]:
        return {
            "descricao": descricao,
            "confianca": confianca,
            "origem": origem,
        }

    def _montar_resposta(self, aprendizados: list[dict[str, Any]]) -> str:
        if not aprendizados:
            return "Ainda nao tenho aprendizados registrados."

        linhas = ["Aprendizados:"]
        for aprendizado in aprendizados:
            linhas.append(
                "- "
                f"{aprendizado.get('descricao') or 'sem descricao'} "
                f"(confianca: {aprendizado.get('confianca')})"
            )
        return "\n".join(linhas)

    def _agora(self) -> str:
        """Retorna timestamp atual em UTC."""
        return datetime.now(timezone.utc).isoformat()
