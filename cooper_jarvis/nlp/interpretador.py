"""Interpretador inicial do Cooper Jarvis."""

import re
import unicodedata
from typing import Any


class Interpretador:
    """Transforma texto bruto em uma analise simples."""

    def interpretar(self, texto: str) -> dict[str, Any]:
        """Interpreta texto sem executar nenhuma acao."""
        texto_limpo = str(texto or "").strip()
        texto_normalizado = self._normalizar(texto_limpo)
        return {
            "texto_original": texto,
            "texto_normalizado": texto_normalizado,
            "intencao": self._identificar_intencao(texto_normalizado),
            "entidades": self._extrair_entidades(texto_limpo, texto_normalizado),
        }

    def _identificar_intencao(self, texto: str) -> str:
        """Identifica intencoes basicas sem executar acoes."""
        termos_contexto = {
            "contexto",
            "ultimo comando",
            "ultima resposta",
            "ultimo agente",
        }
        if any(termo in texto for termo in termos_contexto):
            return "contexto_consultar"

        termos_historico = {
            "historico",
            "historico de conversa",
            "ultimas conversas",
            "ultimos eventos",
        }
        if any(termo in texto for termo in termos_historico):
            return "historico_consultar"

        if self._extrair_consulta_memoria_operacional(texto):
            return "memoria_operacional_consultar"

        termos_memoria_operacional = {
            "memoria operacional",
            "o que voce sabe",
            "fatos salvos",
            "meus projetos",
            "minhas preferencias",
            "caminhos importantes",
            "dispositivos conhecidos",
        }
        if any(termo in texto for termo in termos_memoria_operacional):
            return "memoria_operacional_consultar"

        if self._extrair_memoria_operacional(texto):
            return "memoria_operacional_registrar"

        return "conversa"

    def _extrair_entidades(
        self,
        texto_original: str,
        texto_normalizado: str,
    ) -> dict[str, Any]:
        """Extrai entidades simples sem executar acoes."""
        return {
            "memoria_operacional": self._extrair_memoria_operacional(
                texto_normalizado,
                texto_original=texto_original,
            ),
            "chave_memoria_operacional": (
                self._extrair_consulta_memoria_operacional(texto_normalizado)
            ),
            "categoria_memoria_operacional": (
                self._extrair_categoria_memoria(texto_normalizado)
            ),
        }

    def _extrair_memoria_operacional(
        self,
        texto: str,
        texto_original: str | None = None,
    ) -> dict[str, str] | None:
        """Extrai frases afirmativas que devem ser gravadas."""
        fonte = texto_original or texto
        nome = self._extrair_por_regex(
            fonte,
            [
                r"\bmeu\s+nome\s+(?:e|eh|\u00e9)\s+(.+)$",
                r"\beu\s+me\s+chamo\s+(.+)$",
                r"\bme\s+chamo\s+(.+)$",
            ],
        )
        if nome:
            return {
                "chave": "nome_usuario",
                "valor": self._limpar_valor(nome).title(),
                "categoria": "usuario",
            }

        projeto = self._extrair_por_regex(
            fonte,
            [
                r"\bmeu\s+projeto\s+principal\s+(?:e|eh|\u00e9)\s+(.+)$",
                r"\bprojeto\s+principal\s+(?:e|eh|\u00e9)\s+(.+)$",
            ],
        )
        if projeto:
            return {
                "chave": "projeto_principal",
                "valor": self._limpar_valor(projeto),
                "categoria": "projetos",
            }

        editor = self._extrair_por_regex(
            fonte,
            [
                r"\bmeu\s+editor\s+(?:e|eh|\u00e9)\s+(.+)$",
                r"\buso\s+(?:o\s+)?editor\s+(.+)$",
            ],
        )
        if editor:
            return {
                "chave": "editor_principal",
                "valor": self._limpar_valor(editor),
                "categoria": "preferencias",
            }

        preferencia = self._extrair_por_regex(
            fonte,
            [
                r"\bprefiro\s+(.+)$",
                r"\bminha\s+preferencia\s+(?:e|eh|\u00e9)\s+(.+)$",
            ],
        )
        if preferencia:
            return {
                "chave": "preferencia_geral",
                "valor": self._limpar_valor(preferencia),
                "categoria": "preferencias",
            }

        caminho = self._extrair_por_regex(
            fonte,
            [
                r"\bcaminho\s+(?:do|da|de)\s+(.+?)\s+(?:e|eh|\u00e9)\s+(.+)$",
                r"\b(.+?)\s+fica\s+em\s+(.+)$",
                r"\bcaminho\s+importante\s+(.+)$",
            ],
        )
        if caminho:
            partes = caminho if isinstance(caminho, tuple) else ("geral", caminho)
            return {
                "chave": f"caminho_{self._chave(partes[0])}",
                "valor": self._limpar_valor(partes[1]),
                "categoria": "caminhos",
            }

        dispositivo = self._extrair_por_regex(
            fonte,
            [
                r"\bdispositivo\s+(?:conhecido\s+)?(.+)$",
            ],
        )
        if dispositivo:
            valor = self._limpar_valor(dispositivo)
            return {
                "chave": f"dispositivo_{self._chave(valor)}",
                "valor": valor,
                "categoria": "dispositivos",
            }

        generica = self._extrair_por_regex(
            fonte,
            [
                r"\bmemor(?:ize|izar)\s+(.+?)\s*:\s*(.+)$",
                r"\bguarde\s+(.+?)\s*:\s*(.+)$",
            ],
        )
        if generica:
            partes = generica if isinstance(generica, tuple) else ("geral", generica)
            return {
                "chave": self._chave(partes[0]),
                "valor": self._limpar_valor(partes[1]),
                "categoria": self._categoria_por_texto(texto),
            }

        return None

    def _extrair_consulta_memoria_operacional(self, texto: str) -> str | None:
        """Identifica perguntas que devem consultar fatos ja salvos."""
        consultas = {
            "nome_usuario": [
                r"\bqual\s+(?:e\s+)?(?:o\s+)?meu\s+nome\b",
                r"\bcomo\s+eu\s+me\s+chamo\b",
            ],
            "projeto_principal": [
                r"\bqual\s+(?:e\s+)?(?:o\s+)?meu\s+projeto\s+principal\b",
                r"\bqual\s+projeto\s+principal\b",
            ],
            "editor_principal": [
                r"\bqual\s+editor\s+eu\s+uso\b",
                r"\bqual\s+(?:e\s+)?(?:o\s+)?meu\s+editor\b",
            ],
        }

        for chave, padroes in consultas.items():
            if self._extrair_por_regex(texto, padroes) is not None:
                return chave

        caminho = self._extrair_por_regex(
            texto,
            [
                r"\bonde\s+fica\s+(?:o\s+)?(.+)$",
                r"\bqual\s+(?:e\s+)?(?:o\s+)?caminho\s+(?:do|da|de)\s+(.+)$",
            ],
        )
        if caminho:
            return f"caminho_{self._chave(caminho)}"

        return None

    def _extrair_categoria_memoria(self, texto: str) -> str | None:
        """Extrai categoria de consulta da memoria operacional."""
        if "projeto" in texto:
            return "projetos"
        if "preferencia" in texto or "prefiro" in texto or "editor" in texto:
            return "preferencias"
        if "caminho" in texto or "onde fica" in texto:
            return "caminhos"
        if "dispositivo" in texto:
            return "dispositivos"
        if "usuario" in texto or "sobre mim" in texto or "nome" in texto:
            return "usuario"
        return None

    def _categoria_por_texto(self, texto: str) -> str:
        """Infere categoria basica a partir do texto interpretado."""
        return self._extrair_categoria_memoria(texto) or "geral"

    def _extrair_por_regex(
        self,
        texto: str,
        padroes: list[str],
    ) -> str | tuple[str, ...] | None:
        """Extrai valor usando padroes simples."""
        for padrao in padroes:
            encontrado = re.search(padrao, texto, flags=re.IGNORECASE)
            if encontrado:
                grupos = encontrado.groups()
                if len(grupos) == 1:
                    return grupos[0].strip()
                return tuple(grupo.strip() for grupo in grupos)
        return None

    def _limpar_valor(self, valor: str) -> str:
        """Limpa pontuacao simples do valor extraido."""
        return " ".join(str(valor or "").strip(" .,:;?").split())

    def _chave(self, valor: str) -> str:
        """Cria uma chave simples para memoria operacional."""
        texto = self._normalizar(valor)
        texto = re.sub(r"[^a-z0-9]+", "_", texto)
        return texto.strip("_") or "geral"

    def _normalizar(self, texto: str) -> str:
        """Normaliza texto para facilitar a interpretacao."""
        texto_normalizado = " ".join(texto.lower().split())
        texto_normalizado = unicodedata.normalize("NFD", texto_normalizado)
        return "".join(
            caractere
            for caractere in texto_normalizado
            if unicodedata.category(caractere) != "Mn"
        )
