"""Agente de acoes do sistema operacional."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
import subprocess
from typing import Any

from agents.base_agent import BaseAgent
from repositories.sistema_repository import SistemaRepository


class SistemaAgent(BaseAgent):
    """Executa acoes simples no sistema operacional."""

    nome = "sistema"

    ACOES = {
        "abrir_bloco_de_notas": {
            "comando": r"C:\Windows\System32\notepad.exe",
            "nome": "bloco de notas",
        },
        "abrir_calculadora": {
            "comando": "calc.exe",
            "nome": "calculadora",
        },
        "abrir_vscode": {
            "comando": "code",
            "nome": "VS Code",
        },
        "abrir_explorador": {
            "comando": "explorer.exe",
            "nome": "explorador de arquivos",
        },
    }

    def __init__(
        self,
        repository: SistemaRepository | None = None,
        executor: Callable[[str], None] | None = None,
    ) -> None:
        self.repository = repository or SistemaRepository()
        self.executor = executor or self._executar_comando

    def pode_processar(self, analise: dict[str, Any]) -> bool:
        """Identifica pedidos de execucao no sistema."""
        return analise.get("intencao") == "sistema_executar"

    def processar(self, analise: dict[str, Any]) -> dict[str, Any]:
        """Executa a acao solicitada e registra log."""
        entidades = analise.get("entidades") or {}
        acao = entidades.get("acao_sistema")
        comando_usuario = analise.get("texto_original") or ""

        if acao not in self.ACOES:
            resultado = "acao_nao_suportada"
            self._registrar_log(comando_usuario, resultado)
            return self._resposta(
                "Ainda nao sei executar essa acao do sistema.",
                acao,
                resultado,
            )

        configuracao = self.ACOES[acao]
        try:
            self.executor(configuracao["comando"])
        except Exception as erro:
            resultado = f"erro: {erro}"
            self._registrar_log(comando_usuario, resultado)
            return self._resposta(
                f"Nao consegui abrir {configuracao['nome']}.",
                acao,
                resultado,
            )

        resultado = "executado"
        self._registrar_log(comando_usuario, resultado)
        return self._resposta(
            f"Abrindo {configuracao['nome']}.",
            acao,
            resultado,
        )

    def _executar_comando(self, comando: str) -> None:
        """Executa um comando fixo do sistema."""
        subprocess.Popen(comando, shell=True)

    def _registrar_log(self, comando: str, resultado: str) -> dict[str, Any]:
        log = {
            "comando": comando,
            "resultado": resultado,
            "timestamp": self._agora(),
        }
        return self.repository.registrar(log)

    def _resposta(
        self,
        mensagem: str,
        acao: str | None,
        resultado: str,
    ) -> dict[str, Any]:
        return {
            "agent": self.nome,
            "tipo": "sistema",
            "dados": {
                "mensagem": mensagem,
                "acao": acao,
                "resultado": resultado,
            },
        }

    def _agora(self) -> str:
        """Retorna timestamp atual em UTC."""
        return datetime.now(timezone.utc).isoformat()
