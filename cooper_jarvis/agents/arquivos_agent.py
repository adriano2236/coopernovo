"""Agente de acoes seguras com arquivos e pastas."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
from typing import Any

from agents.base_agent import BaseAgent
from repositories.arquivos_repository import ArquivosRepository


class ArquivosAgent(BaseAgent):
    """Executa acoes seguras com arquivos locais."""

    nome = "arquivos"

    def __init__(
        self,
        repository: ArquivosRepository | None = None,
        raiz_cooper: str | Path | None = None,
        executor_abrir: Callable[[Path], None] | None = None,
    ) -> None:
        self.repository = repository or ArquivosRepository()
        self.raiz_cooper = Path(raiz_cooper or Path(__file__).resolve().parents[2])
        self.anotacoes_dir = (
            Path(__file__).resolve().parents[1] / "data" / "anotacoes"
        )
        self.executor_abrir = executor_abrir or self._abrir_pasta

    def pode_processar(self, analise: dict[str, Any]) -> bool:
        """Identifica pedidos seguros de arquivos."""
        return analise.get("intencao") == "arquivos_executar"

    def processar(self, analise: dict[str, Any]) -> dict[str, Any]:
        """Executa a acao de arquivos solicitada."""
        entidades = analise.get("entidades") or {}
        acao = entidades.get("acao_arquivos")
        dados = entidades.get("dados_arquivos") or {}
        comando = analise.get("texto_original") or ""

        if acao == "abrir_pasta_cooper":
            return self._executar_abrir_pasta(comando)
        if acao == "listar_pasta_cooper":
            return self._executar_listar_pasta(comando)
        if acao == "criar_pasta":
            return self._executar_criar_pasta(comando, dados)
        if acao == "criar_anotacao":
            return self._executar_criar_anotacao(comando, dados)

        return self._finalizar(
            comando=comando,
            acao=str(acao or "desconhecida"),
            caminho="",
            resultado="acao_nao_suportada",
            mensagem="Ainda nao sei executar essa acao de arquivos.",
        )

    def _executar_abrir_pasta(self, comando: str) -> dict[str, Any]:
        try:
            self.executor_abrir(self.raiz_cooper)
        except Exception as erro:
            return self._finalizar(
                comando,
                "abrir_pasta_cooper",
                self.raiz_cooper,
                f"erro: {erro}",
                "Nao consegui abrir a pasta Cooper.",
            )

        return self._finalizar(
            comando,
            "abrir_pasta_cooper",
            self.raiz_cooper,
            "executado",
            f"Abrindo pasta Cooper: {self.raiz_cooper}",
        )

    def _executar_listar_pasta(self, comando: str) -> dict[str, Any]:
        itens = self.repository.listar(self.raiz_cooper)
        if not itens:
            return self._finalizar(
                comando,
                "listar_pasta_cooper",
                self.raiz_cooper,
                "sem_itens",
                "Nao encontrei arquivos principais na pasta Cooper.",
            )

        linhas = ["Arquivos principais da pasta Cooper:"]
        for item in itens:
            linhas.append(f"- {item['nome']} ({item['tipo']})")

        return self._finalizar(
            comando,
            "listar_pasta_cooper",
            self.raiz_cooper,
            "executado",
            "\n".join(linhas),
        )

    def _executar_criar_pasta(
        self,
        comando: str,
        dados: dict[str, Any],
    ) -> dict[str, Any]:
        nome = self._nome_seguro(str(dados.get("nome") or ""))
        if not nome:
            return self._finalizar(
                comando,
                "criar_pasta",
                self.raiz_cooper,
                "nome_invalido",
                "Informe o nome da pasta que devo criar.",
            )

        caminho = self.raiz_cooper / nome
        caminho.mkdir(parents=True, exist_ok=True)

        return self._finalizar(
            comando,
            "criar_pasta",
            caminho,
            "executado",
            f"Pasta criada: {caminho}",
        )

    def _executar_criar_anotacao(
        self,
        comando: str,
        dados: dict[str, Any],
    ) -> dict[str, Any]:
        conteudo = str(dados.get("texto") or "").strip()
        if not conteudo:
            return self._finalizar(
                comando,
                "criar_anotacao",
                self.anotacoes_dir,
                "texto_vazio",
                "Informe o texto da anotacao.",
            )

        self.anotacoes_dir.mkdir(parents=True, exist_ok=True)
        nome_arquivo = self._nome_arquivo_anotacao(conteudo)
        caminho = self.anotacoes_dir / nome_arquivo
        caminho.write_text(conteudo + "\n", encoding="utf-8")

        return self._finalizar(
            comando,
            "criar_anotacao",
            caminho,
            "executado",
            f"Anotacao criada: {caminho}",
        )

    def _abrir_pasta(self, caminho: Path) -> None:
        """Abre uma pasta local no Explorador de Arquivos."""
        subprocess.Popen(["explorer.exe", str(caminho)])

    def _finalizar(
        self,
        comando: str,
        acao: str,
        caminho: str | Path,
        resultado: str,
        mensagem: str,
    ) -> dict[str, Any]:
        caminho_texto = str(caminho)
        self.repository.registrar(
            {
                "comando": comando,
                "acao": acao,
                "caminho": caminho_texto,
                "resultado": resultado,
                "timestamp": self._agora(),
            }
        )
        return {
            "agent": self.nome,
            "tipo": "arquivos",
            "dados": {
                "mensagem": mensagem,
                "acao": acao,
                "caminho": caminho_texto,
                "resultado": resultado,
            },
        }

    def _nome_seguro(self, nome: str) -> str:
        """Remove caracteres perigosos de nomes simples."""
        nome_limpo = re.sub(r'[\\/:*?"<>|]+', " ", nome)
        return " ".join(nome_limpo.strip().split())

    def _nome_arquivo_anotacao(self, conteudo: str) -> str:
        """Cria um nome simples para arquivo de anotacao."""
        base = self._nome_seguro(conteudo.lower())
        base = re.sub(r"[^a-z0-9 ]+", "", base)
        base = "_".join(base.split())[:40] or "anotacao"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{base}.txt"

    def _agora(self) -> str:
        """Retorna timestamp atual em UTC."""
        return datetime.now(timezone.utc).isoformat()
