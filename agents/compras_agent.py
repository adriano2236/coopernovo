"""
Agente de compras do Cooper.

Este módulo define o ComprasAgent, responsável por reconhecer e processar
mensagens relacionadas a compras, fornecedores, cotações e reposição. O agente
segue o contrato definido por BaseAgent e retorna apenas dados estruturados.

Regra arquitetural principal:
    ComprasAgent = lógica de domínio de compras em formato DATA ONLY
"""

from typing import Any, Optional, Tuple
import sqlite3
from datetime import datetime

from agents.base_agent import BaseAgent


class ComprasAgent(BaseAgent):
    """
    Agente especializado em registro e solicitações de compras.

    Este agente identifica intenções ligadas a compras, realiza validações de
    dados, registra operações no banco, atualiza o estoque e dispara eventos,
    sempre retornando apenas dados estruturados.
    """

    PALAVRAS_CHAVE = {
        "compra",
        "compras",
        "comprar",
        "comprei",
    }

    def __init__(self, event_bus: Optional[Any] = None, db_file: str = "cooper.db") -> None:
        """
        Inicializa o agente de compras.

        Args:
            event_bus: Barramento de eventos para comunicação com outros módulos.
            db_file: Caminho do arquivo do banco de dados (para testes).
        """
        super().__init__(nome="compra")
        self.event_bus = event_bus
        self.db_file = db_file

    def pode_processar(self, msg: str) -> bool:
        """
        Verifica se a mensagem parece pertencer ao domínio de compras.

        Args:
            msg: Mensagem original enviada ao Cooper.

        Returns:
            True quando a mensagem contém termos associados a compras.
        """
        texto = (msg or "").lower()
        return any(palavra in texto for palavra in self.PALAVRAS_CHAVE)

    def processar(self, msg: str, analise: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        Processa o registro de uma compra: extrai dados, valida, registra no banco,
        atualiza cadastro/estoque e dispara evento.

        Args:
            msg: Mensagem original enviada ao Cooper.
            analise: Resultado da camada de NLP com entidades extraídas.

        Returns:
            Dicionário padronizado com o resultado do processamento.
        """
        # Extração de dados (prioriza o que vier da análise NLP)
        codigo, qtd, preco, produto = self._extrair_dados(msg, analise)

        # ========== VALIDAÇÕES ==========
        if qtd <= 0:
            return self.resposta_padrao(
                status="erro",
                tipo="compra",
                erro="quantidade_invalida"
            )

        if preco <= 0:
            return self.resposta_padrao(
                status="erro",
                tipo="compra",
                erro="preco_invalido"
            )

        if not codigo:
            return self.resposta_padrao(
                status="erro",
                tipo="compra",
                erro="codigo_ausente"
            )

        # ========== REGISTRA COMPRA E ATUALIZA PRODUTO ==========
        try:
            dados_operacao = self._executar_registro(codigo, produto, qtd, preco)
        except sqlite3.Error as e:
            return self.resposta_padrao(
                status="erro",
                tipo="compra",
                dados={
                    "codigo": codigo,
                    "detalhe": str(e)
                },
                erro="falha_operacao_bd"
            )

        # ========== EVENTO ==========
        if self.event_bus and hasattr(self.event_bus, 'emitir'):  # ← verificação segura
            self.event_bus.emitir("compra_realizada", dados_operacao)

        # ========== SUCESSO - RETORNO DE DADOS ==========
        return self.resposta_padrao(
            status="ok",
            tipo="compra",
            dados=dados_operacao
        )

    # -------------------------
    # MÉTODOS AUXILIARES
    # -------------------------
    def _extrair_dados(self, msg: str, analise: Optional[dict[str, Any]]) -> Tuple[Optional[str], int, float, str]:
        """Extrai código, quantidade, preço e nome do produto da mensagem ou da análise."""
        if analise and isinstance(analise, dict):
            entidades = analise.get("entidades", {})
            codigo = entidades.get("codigo")
            try:
                qtd = int(entidades.get("quantidade", 0))
            except (TypeError, ValueError):
                qtd = 0
            
            try:
                preco = float(entidades.get("preco", 0))
            except (TypeError, ValueError):
                preco = 0.0
            produto = str(entidades.get("produto", "produto"))
            
            # Fallback: extrair da mensagem se necessário
            if not codigo:
                codigo = self._extrair_codigo_da_mensagem(msg)
                
            return codigo, qtd, preco, produto

        # Fallback completo
        return self._extrair_codigo_da_mensagem(msg), 0, 0.0, "produto"

    def _extrair_codigo_da_mensagem(self, msg: str) -> Optional[str]:
        """Extrai código numérico da mensagem (fallback simples)."""
        palavras = msg.split()
        for palavra in palavras:
            if palavra.isdigit() and len(palavra) >= 3:
                return palavra
        return None

    def _executar_registro(self, codigo: str, produto: str, qtd: int, preco: float) -> dict[str, Any]:
        """Executa todo o fluxo no banco: insere compra, verifica e atualiza/cria produto."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            total = qtd * preco
            data = datetime.now().isoformat()

            # 1. Insere registro da compra
            cursor.execute('''
                INSERT INTO compras (codigo, produto, quantidade, preco, total, data)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (codigo, produto, qtd, preco, total, data))

            # 2. Verifica se produto já está cadastrado
            cursor.execute('SELECT estoque, nome FROM produtos WHERE codigo = ?', (codigo,))
            resultado = cursor.fetchone()

            if resultado:
                nome_atual = resultado[1]
                # Usa nome existente se disponível
                nome_produto = nome_atual or produto
                # Atualiza estoque e custo médio
                cursor.execute('''
                    UPDATE produtos 
                    SET estoque = estoque + ?, 
                        custo_medio = CASE 
                            WHEN custo_medio IS NULL THEN ?
                            ELSE (custo_medio + ?) / 2 
                        END
                    WHERE codigo = ?
                ''', (qtd, preco, preco, codigo))
            else:
                nome_produto = produto
                # Cadastra produto novo
                cursor.execute('''
                    INSERT INTO produtos (codigo, nome, estoque, custo_medio)
                    VALUES (?, ?, ?, ?)
                ''', (codigo, nome_produto, qtd, preco))

            conn.commit()

            return {
                "codigo": codigo,
                "produto": nome_produto,
                "quantidade": qtd,
                "preco_unitario": preco,
                "total": total,
                "data": data
            }