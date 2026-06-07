"""
Agente de vendas do Cooper.

Este módulo define o VendasAgent, responsável por reconhecer e processar
mensagens relacionadas a vendas. O agente segue o contrato definido por
BaseAgent e retorna apenas dados estruturados.

Regra arquitetural principal:
    VendasAgent = lógica de domínio de vendas em formato DATA ONLY
"""

from typing import Any, Optional, Tuple
import sqlite3
from datetime import datetime

from agents.base_agent import BaseAgent


class VendasAgent(BaseAgent):
    """
    Agente especializado em solicitações e registro de vendas.

    Este agente identifica intenções ligadas a vendas, realiza validações,
    acessa o banco de dados e registra a operação, seguindo estritamente
    o modelo DATA ONLY.
    """

    PALAVRAS_CHAVE = {
        "venda",
        "vendas",
        "vende",
        "vendi",
        "vender",
        "vendido",
    }

    def __init__(self, event_bus: Optional[Any] = None, db_file: str = "cooper.db") -> None:
        """
        Inicializa o agente de vendas.

        Args:
            event_bus: Barramento de eventos para comunicação com outros módulos.
            db_file: Caminho do arquivo do banco de dados.
        """
        super().__init__(nome="venda")
        self.event_bus = event_bus
        self.db_file = db_file  # ← permite injeção para testes

    def pode_processar(self, msg: str) -> bool:
        """
        Verifica se a mensagem parece pertencer ao domínio de vendas.

        Args:
            msg: Mensagem original enviada ao Cooper.

        Returns:
            True quando a mensagem contém termos associados a vendas.
        """
        texto = (msg or "").lower()
        return any(palavra in texto for palavra in self.PALAVRAS_CHAVE)

    def processar(self, msg: str, analise: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        Processa o registro de uma venda: extrai dados, valida, consulta estoque,
        registra operação e dispara evento.

        Args:
            msg: Mensagem original enviada ao Cooper.
            analise: Resultado da camada de NLP com entidades extraídas.

        Returns:
            Dicionário padronizado com o resultado do processamento.
        """
        # Extração de dados (prioriza análise do NLP)
        codigo, qtd = self._extrair_dados(msg, analise)

        # Validações iniciais
        if qtd <= 0:
            return self.resposta_padrao(
                status="erro",
                tipo="venda",
                erro="quantidade_invalida"
            )

        if not codigo:
            return self.resposta_padrao(
                status="erro",
                tipo="venda",
                erro="codigo_ausente"
            )

        # Acesso ao banco e validações de produto/estoque
        try:
            produto = self._buscar_produto(codigo)
        except sqlite3.Error as e:
            return self.resposta_padrao(
                status="erro",
                tipo="venda",
                dados={
                    "codigo": codigo,
                    "detalhe": str(e)
                },
                erro="erro_bd"
            )

        if not produto:
            return self.resposta_padrao(
                status="erro",
                tipo="venda",
                dados={"codigo": codigo},
                erro="produto_nao_encontrado"
            )

        codigo_prod, nome_prod, estoque_prod, preco_prod = produto

        if not preco_prod or preco_prod <= 0:
            return self.resposta_padrao(
                status="erro",
                tipo="venda",
                dados={"produto": nome_prod, "codigo": codigo},
                erro="preco_invalido"
            )

        if estoque_prod < qtd:
            return self.resposta_padrao(
                status="erro",
                tipo="venda",
                dados={
                    "produto": nome_prod,
                    "codigo": codigo,
                    "estoque_disponivel": estoque_prod,
                    "solicitado": qtd
                },
                erro="estoque_insuficiente"
            )

        # Registro da operação
        total = qtd * preco_prod
        data = datetime.now().isoformat()

        try:
            self._registrar_venda(codigo, nome_prod, qtd, preco_prod, total, data)
        except sqlite3.Error as e:
            return self.resposta_padrao(
                status="erro",
                tipo="venda",
                dados={
                    "produto": nome_prod,
                    "codigo": codigo,
                    "detalhe": str(e)
                },
                erro="falha_registro"
            )

        # Dispara evento para o sistema
        if self.event_bus and hasattr(self.event_bus, 'emitir'):
            self.event_bus.emitir("venda_realizada", {
                "codigo": codigo,
                "produto": nome_prod,
                "quantidade": qtd,
                "preco_unitario": preco_prod,
                "total": total
            })

        # Sucesso - retorno de dados estruturados
        return self.resposta_padrao(
            status="ok",
            tipo="venda",
            dados={
                "codigo": codigo,
                "produto": nome_prod,
                "quantidade": qtd,
                "preco_unitario": preco_prod,
                "total": total,
                "data": data
            }
        )

    # -------------------------
    # MÉTODOS AUXILIARES
    # -------------------------
    def _extrair_dados(self, msg: str, analise: Optional[dict[str, Any]]) -> Tuple[Optional[str], int]:
        """Extrai código e quantidade da mensagem ou da análise NLP."""
        if analise and isinstance(analise, dict):
            entidades = analise.get("entidades", {})
            codigo = entidades.get("codigo")
            qtd = entidades.get("quantidade", 1)
            
            # Tenta extrair da mensagem se não veio na análise
            if not codigo:
                codigo = self._extrair_codigo_da_mensagem(msg)
                
            return codigo, int(qtd) if qtd else 1
        
        # Fallback: extrair diretamente da mensagem
        codigo = self._extrair_codigo_da_mensagem(msg)
        return codigo, 1

    def _extrair_codigo_da_mensagem(self, msg: str) -> Optional[str]:
        """Extrai código numérico da mensagem (fallback simples)."""
        # Exemplo: extrai números com 3+ dígitos como possível código
        palavras = msg.split()
        for palavra in palavras:
            if palavra.isdigit() and len(palavra) >= 3:
                return palavra
        return None

    def _buscar_produto(self, codigo: str) -> Optional[Tuple]:
        """Busca dados do produto no banco de dados."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT codigo, nome, estoque, preco_venda
                FROM produtos
                WHERE codigo = ?
            """, (codigo,))

            produto = cursor.fetchone()

        return produto

    def _registrar_venda(self, codigo: str, nome: str, qtd: int, 
                         preco: float, total: float, data: str) -> None:
        """Registra venda e atualiza estoque no banco de dados."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO vendas (
                    codigo,
                    produto,
                    quantidade,
                    preco,
                    total,
                    data
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                codigo,
                nome,
                qtd,
                preco,
                total,
                data
            ))

            cursor.execute("""
                UPDATE produtos
                SET estoque = estoque - ?
                WHERE codigo = ?
            """, (
                qtd,
                codigo
            ))

            conn.commit()