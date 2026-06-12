"""Agente de backup e exportacao do Cooper."""

from datetime import datetime, timezone
from pathlib import Path
import csv
import json
from typing import Any

from agents.base_agent import BaseAgent
from repositories.backup_repository import BackupRepository


class BackupAgent(BaseAgent):
    """Agente responsavel por criar backups e exportacoes de dados."""

    PALAVRAS_CHAVE = {
        "backup",
        "backups",
        "bkp",
        "copia",
        "copiar",
        "copie",
        "csv",
        "excel",
        "exportacao",
        "exportacoes",
        "exportar",
        "exporte",
        "json",
        "planilha",
        "salva",
        "salvar",
        "salve",
    }

    def __init__(
        self,
        repository: BackupRepository | None = None,
        backups_dir: str | Path = "data/backups",
        exportacoes_dir: str | Path = "data/exportacoes",
    ) -> None:
        super().__init__(nome="backup")
        self.repository = repository or BackupRepository()
        self.backups_dir = Path(backups_dir)
        self.exportacoes_dir = Path(exportacoes_dir)

    def pode_processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> bool:
        if analise:
            return analise.get("dominio") == "backup"

        texto = (msg or "").lower()
        return any(palavra in texto for palavra in self.PALAVRAS_CHAVE)

    def processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        intencao = str((analise or {}).get("intencao") or "backup_criar")
        entidades = self.entidades(analise)
        formato = entidades.get("formato_exportacao") or "json"
        resultado = self._executar_acao(intencao=intencao, formato=formato)

        dados = {
            "mensagem_original": msg,
            "resumo": self._resumo(intencao),
            "acao": self._acao(intencao),
            "formato": formato,
            "entidades": entidades,
            "campos_necessarios": [],
            "proximas_acoes": ["guardar arquivo em local seguro"],
            "resultado": resultado,
        }

        return self.resposta_padrao(status="sucesso", tipo=intencao, dados=dados)

    def _resumo(self, intencao: str) -> str:
        resumos = {
            "backup_criar": "Backup do banco criado.",
            "backup_exportar": "Exportacao de dados criada.",
            "backup_listar": "Backups e exportacoes recuperados.",
        }
        return resumos.get(intencao, "Solicitacao de backup identificada.")

    def _acao(self, intencao: str) -> str:
        acoes = {
            "backup_criar": "criar_backup_sqlite",
            "backup_exportar": "exportar_dados",
            "backup_listar": "listar_backups_exportacoes",
        }
        return acoes.get(intencao, "analisar_backup")

    def _executar_acao(self, intencao: str, formato: str) -> dict[str, Any]:
        if intencao == "backup_listar":
            return self._listar_arquivos()

        if intencao == "backup_exportar":
            return self._exportar(formato=formato)

        return self._criar_backup()

    def _criar_backup(self) -> dict[str, Any]:
        destino = self.backups_dir / f"cooper_backup_{self._timestamp()}.db"
        return self.repository.criar_backup_sqlite(destino)

    def _exportar(self, formato: str) -> dict[str, Any]:
        snapshot = self.repository.exportar_snapshot()
        if snapshot.get("tipo_resultado") == "backup_nao_encontrado":
            return snapshot

        if formato == "csv":
            return self._exportar_csv(snapshot)

        return self._exportar_json(snapshot)

    def _exportar_json(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        self.exportacoes_dir.mkdir(parents=True, exist_ok=True)
        destino = self.exportacoes_dir / f"cooper_export_{self._timestamp()}.json"
        destino.write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        return {
            "tipo_resultado": "exportacao_arquivo",
            "formato": "json",
            "caminho": str(destino),
            "tamanho_bytes": destino.stat().st_size,
            "total_tabelas": snapshot.get("total_tabelas", 0),
            "total_registros": snapshot.get("total_registros", 0),
            "tabelas": self._resumo_tabelas(snapshot),
            "criado_em": self._agora(),
        }

    def _exportar_csv(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        destino_dir = self.exportacoes_dir / f"cooper_csv_{self._timestamp()}"
        destino_dir.mkdir(parents=True, exist_ok=True)
        arquivos = []

        for tabela in snapshot.get("tabelas", []):
            nome_tabela = str(tabela.get("nome") or "tabela")
            colunas = tabela.get("colunas") or []
            registros = tabela.get("registros") or []
            destino = destino_dir / f"{self._nome_arquivo(nome_tabela)}.csv"
            with destino.open("w", newline="", encoding="utf-8") as arquivo:
                writer = csv.DictWriter(arquivo, fieldnames=colunas)
                writer.writeheader()
                writer.writerows(registros)
            arquivos.append(str(destino))

        manifest = destino_dir / "manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "gerado_em": snapshot.get("gerado_em"),
                    "origem": snapshot.get("origem"),
                    "total_tabelas": snapshot.get("total_tabelas", 0),
                    "total_registros": snapshot.get("total_registros", 0),
                    "arquivos": arquivos,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        arquivos.append(str(manifest))

        return {
            "tipo_resultado": "exportacao_arquivo",
            "formato": "csv",
            "caminho": str(destino_dir),
            "arquivos": arquivos,
            "total_tabelas": snapshot.get("total_tabelas", 0),
            "total_registros": snapshot.get("total_registros", 0),
            "tabelas": self._resumo_tabelas(snapshot),
            "criado_em": self._agora(),
        }

    def _listar_arquivos(self) -> dict[str, Any]:
        backups = self._listar_caminhos(self.backups_dir, padroes=("*.db",))
        exportacoes = self._listar_caminhos(
            self.exportacoes_dir,
            padroes=("*.json",),
            incluir_diretorios=True,
        )
        return {
            "tipo_resultado": "backup_lista",
            "backups": backups,
            "exportacoes": exportacoes,
            "total_backups": len(backups),
            "total_exportacoes": len(exportacoes),
        }

    def _listar_caminhos(
        self,
        pasta: Path,
        padroes: tuple[str, ...],
        incluir_diretorios: bool = False,
    ) -> list[dict[str, Any]]:
        if not pasta.exists():
            return []

        caminhos = []
        for padrao in padroes:
            caminhos.extend(pasta.glob(padrao))

        if incluir_diretorios:
            caminhos.extend(caminho for caminho in pasta.iterdir() if caminho.is_dir())

        itens = []
        for caminho in sorted(caminhos, key=lambda item: item.stat().st_mtime, reverse=True):
            stat = caminho.stat()
            itens.append(
                {
                    "nome": caminho.name,
                    "caminho": str(caminho),
                    "tamanho_bytes": stat.st_size if caminho.is_file() else None,
                    "tipo_arquivo": "pasta" if caminho.is_dir() else caminho.suffix.lstrip("."),
                    "modificado_em": datetime.fromtimestamp(
                        stat.st_mtime,
                        tz=timezone.utc,
                    ).isoformat(),
                }
            )
        return itens

    def _resumo_tabelas(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "nome": tabela.get("nome"),
                "total_registros": tabela.get("total_registros", 0),
            }
            for tabela in snapshot.get("tabelas", [])
        ]

    def _nome_arquivo(self, nome: str) -> str:
        partes = []
        for caractere in (nome or "").lower():
            if caractere.isalnum():
                partes.append(caractere)
            elif caractere in {"_", "-"}:
                partes.append(caractere)
            else:
                partes.append("_")
        return "".join(partes).strip("_") or "tabela"

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    def _agora(self) -> str:
        return datetime.now(timezone.utc).isoformat()
