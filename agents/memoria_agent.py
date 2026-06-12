"""Agente de memoria do Cooper."""

from typing import Any

from agents.base_agent import BaseAgent
from repositories.memoria_repository import MemoriaRepository


class MemoriaAgent(BaseAgent):
    """Agente responsavel por registrar e consultar memorias."""

    PALAVRAS_CHAVE = {
        "apague",
        "esqueca",
        "esquecer",
        "guarde",
        "guardar",
        "historico",
        "lembra",
        "lembre",
        "memoria",
        "memorias",
        "memoriza",
        "memorize",
    }

    def __init__(self, repository: MemoriaRepository | None = None) -> None:
        super().__init__(nome="memoria")
        self.repository = repository or MemoriaRepository()

    def pode_processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> bool:
        if analise:
            return analise.get("dominio") == "memoria"

        texto = (msg or "").lower()
        return any(palavra in texto for palavra in self.PALAVRAS_CHAVE)

    def processar(
        self,
        msg: str,
        analise: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        intencao = str((analise or {}).get("intencao") or "memoria_listar")
        entidades = self.entidades(analise)
        texto_memoria = entidades.get("memoria_texto")
        busca = entidades.get("busca_memoria") or texto_memoria
        fase = self._converter_fase(entidades.get("fase_memoria"))
        resultado = self._executar_acao(
            intencao=intencao,
            texto_memoria=texto_memoria,
            busca=busca,
            fase=fase,
        )

        dados = {
            "mensagem_original": msg,
            "resumo": self._resumo(intencao),
            "acao": self._acao(intencao),
            "entidades": entidades,
            "fase": fase,
            "campos_necessarios": self._campos_necessarios(
                intencao=intencao,
                texto_memoria=texto_memoria,
                busca=busca,
            ),
            "proximas_acoes": self._proximas_acoes(intencao),
            "resultado": resultado,
        }

        return self.resposta_padrao(status="sucesso", tipo=intencao, dados=dados)

    def aprender_com_evento(
        self,
        texto: str,
        analise: dict[str, Any] | None,
        resultado: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Aprende memorias automaticas a partir de eventos processados."""
        if not isinstance(resultado, dict):
            return {"tipo_resultado": "memoria_aprendizado", "itens": []}

        if resultado.get("agente") == self.nome:
            return {"tipo_resultado": "memoria_aprendizado", "itens": []}

        memorias = []
        memorias.extend(self._aprender_contexto(analise))
        memorias.extend(self._aprender_operacional(resultado))
        memorias.extend(self._aprender_uso(analise, resultado))
        memorias.extend(self._aprender_estrategia(resultado))

        return {
            "tipo_resultado": "memoria_aprendizado",
            "texto": texto,
            "itens": [memoria for memoria in memorias if memoria],
        }

    def _resumo(self, intencao: str) -> str:
        resumos = {
            "memoria_guardar": "Memoria registrada.",
            "memoria_listar": "Memorias recuperadas.",
            "memoria_historico": "Historico de conversa recuperado.",
            "memoria_esquecer": "Memoria removida.",
        }
        return resumos.get(intencao, "Solicitacao de memoria identificada.")

    def _acao(self, intencao: str) -> str:
        acoes = {
            "memoria_guardar": "guardar_memoria",
            "memoria_listar": "listar_memorias",
            "memoria_historico": "listar_historico",
            "memoria_esquecer": "esquecer_memoria",
        }
        return acoes.get(intencao, "analisar_memoria")

    def _campos_necessarios(
        self,
        intencao: str,
        texto_memoria: str | None,
        busca: str | None,
    ) -> list[str]:
        if intencao == "memoria_guardar" and not texto_memoria:
            return ["informacao_para_guardar"]

        if intencao == "memoria_esquecer" and not busca:
            return ["memoria_ou_termo"]

        return []

    def _proximas_acoes(self, intencao: str) -> list[str]:
        proximas = {
            "memoria_guardar": ["usar memoria como contexto futuro"],
            "memoria_listar": ["consultar memorias importantes"],
            "memoria_historico": ["revisar eventos recentes"],
            "memoria_esquecer": ["manter memoria limpa"],
        }
        return proximas.get(intencao, ["organizar memoria"])

    def _executar_acao(
        self,
        intencao: str,
        texto_memoria: str | None,
        busca: str | None,
        fase: int | None,
    ) -> dict[str, Any] | None:
        if intencao == "memoria_guardar" and texto_memoria:
            fase, tipo, importancia = self._classificar_memoria(texto_memoria)
            return self.repository.registrar_memoria(
                fase=fase,
                tipo=tipo,
                chave=self._chave(texto_memoria),
                valor=texto_memoria,
                origem="usuario",
                importancia=importancia,
                metadados={"captura": "manual"},
            )

        if intencao == "memoria_historico":
            return {
                "tipo_resultado": "memoria_historico",
                "itens": self.repository.listar_eventos(limite=20),
            }

        if intencao == "memoria_esquecer" and busca:
            return {
                "tipo_resultado": "memoria_esquecida",
                "busca": busca,
                "itens": self.repository.desativar_por_busca(busca),
            }

        if intencao == "memoria_listar":
            return {
                "tipo_resultado": "memoria_lista",
                "fase": fase,
                "titulo": self._titulo_fase(fase),
                "itens": self.repository.listar_memorias(limite=20, fase=fase),
            }

        return None

    def _classificar_memoria(self, texto: str) -> tuple[int, str, int]:
        normalizado = texto.lower()

        if any(
            termo in normalizado
            for termo in (
                "estrategia",
                "meta",
                "metas",
                "previsao",
                "sugestao",
                "tendencia",
            )
        ):
            return 5, "estrategica", 5

        if any(
            termo in normalizado
            for termo in ("apelido", "chamo", "costumo chamar", "padrao de uso")
        ):
            return 4, "aprendizado_uso", 4

        if any(
            termo in normalizado
            for termo in (
                "cliente",
                "dobro",
                "estoque",
                "fornecedor",
                "fornecedores",
                "loja",
                "margem",
                "pedido",
                "preferencia",
                "preferencias",
                "prefiro",
                "produto",
                "reembolso",
                "regra",
                "regras",
                "valor da peca",
            )
        ):
            return 3, "operacional", 3

        return 1, "contexto", 2

    def _chave(self, texto: str) -> str:
        palavras = [palavra for palavra in texto.lower().split() if palavra]
        return "-".join(palavras[:6]) or "memoria"

    def _converter_fase(self, valor: Any) -> int | None:
        if valor is None:
            return None

        try:
            fase = int(valor)
        except (TypeError, ValueError):
            return None

        if 1 <= fase <= 5:
            return fase

        return None

    def _titulo_fase(self, fase: int | None) -> str:
        titulos = {
            1: "Contexto imediato",
            2: "Historico de conversa",
            3: "Memoria operacional",
            4: "Aprendizado",
            5: "Memoria estrategica",
        }
        return titulos.get(fase, "Memorias")

    def _aprender_contexto(
        self,
        analise: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        if not isinstance(analise, dict):
            return []

        memorias = []
        dominio = analise.get("dominio")
        intencao = analise.get("intencao")
        entidades = analise.get("entidades") or {}
        produto = entidades.get("produto")
        cliente = entidades.get("cliente")
        fornecedor = entidades.get("fornecedor")
        produto_contextual = produto and (
            dominio not in {"contas", "memoria"}
            or bool(entidades.get("categorias_roupa"))
        )

        if dominio:
            memorias.append(
                self._salvar_memoria_automatica(
                    fase=1,
                    tipo="contexto_imediato",
                    chave="contexto-ultimo-dominio",
                    valor=f"Ultimo dominio: {dominio}",
                    importancia=2,
                    metadados={"campo": "dominio", "valor": dominio},
                )
            )

        if intencao:
            memorias.append(
                self._salvar_memoria_automatica(
                    fase=1,
                    tipo="contexto_imediato",
                    chave="contexto-ultima-intencao",
                    valor=f"Ultima intencao: {intencao}",
                    importancia=2,
                    metadados={"campo": "intencao", "valor": intencao},
                )
            )

        if produto_contextual:
            memorias.append(
                self._salvar_memoria_automatica(
                    fase=1,
                    tipo="contexto_imediato",
                    chave="contexto-ultimo-produto",
                    valor=f"Ultimo produto: {produto}",
                    importancia=2,
                    metadados={"campo": "produto", "valor": produto},
                )
            )

        if cliente:
            memorias.append(
                self._salvar_memoria_automatica(
                    fase=1,
                    tipo="contexto_imediato",
                    chave="contexto-ultimo-cliente",
                    valor=f"Ultimo cliente: {cliente}",
                    importancia=2,
                    metadados={"campo": "cliente", "valor": cliente},
                )
            )

        if fornecedor:
            memorias.append(
                self._salvar_memoria_automatica(
                    fase=1,
                    tipo="contexto_imediato",
                    chave="contexto-ultimo-fornecedor",
                    valor=f"Ultimo fornecedor: {fornecedor}",
                    importancia=2,
                    metadados={"campo": "fornecedor", "valor": fornecedor},
                )
            )

        return memorias

    def _aprender_operacional(
        self,
        resultado: dict[str, Any],
    ) -> list[dict[str, Any]]:
        dados_resultado = self._dados_resultado(resultado)
        if not dados_resultado:
            return []

        tipo = dados_resultado.get("tipo_resultado")
        memorias = []

        if tipo == "pedido":
            pedido_id = dados_resultado.get("pedido_id")
            cliente = dados_resultado.get("cliente")
            produto = dados_resultado.get("produto")
            status = dados_resultado.get("status")
            if pedido_id and cliente and produto:
                memorias.append(
                    self._salvar_memoria_automatica(
                        fase=3,
                        tipo="operacional",
                        chave=f"pedido-{pedido_id}",
                        valor=(
                            f"Pedido #{pedido_id} de {cliente}: "
                            f"{produto} | status {status}"
                        ),
                        importancia=4,
                        metadados={"origem_resultado": "pedido"},
                    )
                )

        if tipo == "conta_receber":
            conta_id = dados_resultado.get("conta_id")
            cliente = dados_resultado.get("cliente")
            valor_total = dados_resultado.get("valor_total")
            valor_pago = dados_resultado.get("valor_pago")
            status = dados_resultado.get("status")
            if conta_id and cliente:
                memorias.append(
                    self._salvar_memoria_automatica(
                        fase=3,
                        tipo="operacional",
                        chave=f"conta-{conta_id}",
                        valor=(
                            f"Conta #{conta_id} de {cliente}: "
                            f"total {self._moeda(valor_total)}, "
                            f"pago {self._moeda(valor_pago)} | status {status}"
                        ),
                        importancia=4,
                        metadados={"origem_resultado": "conta_receber"},
                    )
                )

        if tipo == "cliente":
            cliente_id = dados_resultado.get("cliente_id")
            cliente = dados_resultado.get("cliente")
            telefone = dados_resultado.get("telefone")
            if cliente_id and cliente:
                detalhe = f" | telefone {telefone}" if telefone else ""
                memorias.append(
                    self._salvar_memoria_automatica(
                        fase=3,
                        tipo="operacional",
                        chave=f"cliente-{cliente_id}",
                        valor=f"Cliente #{cliente_id}: {cliente}{detalhe}",
                        importancia=3,
                        metadados={"origem_resultado": "cliente"},
                    )
                )

        if tipo == "fornecedor":
            fornecedor_id = dados_resultado.get("fornecedor_id")
            fornecedor = dados_resultado.get("fornecedor")
            telefone = dados_resultado.get("telefone")
            if fornecedor_id and fornecedor:
                detalhe = f" | telefone {telefone}" if telefone else ""
                memorias.append(
                    self._salvar_memoria_automatica(
                        fase=3,
                        tipo="operacional",
                        chave=f"fornecedor-{fornecedor_id}",
                        valor=f"Fornecedor #{fornecedor_id}: {fornecedor}{detalhe}",
                        importancia=3,
                        metadados={"origem_resultado": "fornecedor"},
                    )
                )

        if tipo == "fornecedor_produto":
            fornecedor = dados_resultado.get("fornecedor")
            produto = dados_resultado.get("produto")
            custo = dados_resultado.get("ultimo_custo")
            if fornecedor and produto:
                detalhe = f" | ultimo custo {self._moeda(custo)}" if custo else ""
                memorias.append(
                    self._salvar_memoria_automatica(
                        fase=3,
                        tipo="operacional",
                        chave=(
                            "fornecedor-produto-"
                            f"{self._chave(str(fornecedor))}-"
                            f"{self._chave(str(produto))}"
                        ),
                        valor=f"{fornecedor} fornece {produto}{detalhe}",
                        importancia=4,
                        metadados={"origem_resultado": "fornecedor_produto"},
                    )
                )

        if tipo == "despesa":
            despesa_id = dados_resultado.get("despesa_id")
            descricao = dados_resultado.get("descricao")
            valor = dados_resultado.get("valor")
            if despesa_id and descricao:
                memorias.append(
                    self._salvar_memoria_automatica(
                        fase=3,
                        tipo="operacional",
                        chave=f"despesa-{despesa_id}",
                        valor=f"Despesa #{despesa_id}: {descricao} por {self._moeda(valor)}",
                        importancia=3,
                        metadados={"origem_resultado": "despesa"},
                    )
                )

        if tipo == "caixa_movimento":
            movimento_id = dados_resultado.get("movimento_id")
            movimento = dados_resultado.get("movimento_tipo")
            valor = dados_resultado.get("valor")
            saldo = dados_resultado.get("saldo_caixa")
            if movimento_id and movimento:
                memorias.append(
                    self._salvar_memoria_automatica(
                        fase=3,
                        tipo="operacional",
                        chave=f"caixa-movimento-{movimento_id}",
                        valor=(
                            f"Caixa: {movimento} de {self._moeda(valor)} "
                            f"| saldo {self._moeda(saldo)}"
                        ),
                        importancia=3,
                        metadados={"origem_resultado": "caixa_movimento"},
                    )
                )

        if tipo in {"backup_arquivo", "exportacao_arquivo"}:
            caminho = dados_resultado.get("caminho")
            formato = dados_resultado.get("formato") or "sqlite"
            if caminho:
                nome_arquivo = str(caminho).replace("\\", "/").split("/")[-1]
                memorias.append(
                    self._salvar_memoria_automatica(
                        fase=3,
                        tipo="operacional",
                        chave=f"{tipo}-{self._chave(nome_arquivo)}",
                        valor=f"{formato.upper()} criado em {caminho}",
                        importancia=3,
                        metadados={"origem_resultado": tipo},
                    )
                )

        venda_id = dados_resultado.get("venda_id")
        if dados_resultado.get("venda_realizada") is True and venda_id:
            produto = dados_resultado.get("produto")
            valor = dados_resultado.get("valor")
            memorias.append(
                self._salvar_memoria_automatica(
                    fase=3,
                    tipo="operacional",
                    chave=f"venda-{venda_id}",
                    valor=f"Venda #{venda_id}: {produto} por {self._moeda(valor)}",
                    importancia=3,
                    metadados={"origem_resultado": "venda"},
                )
            )

        movimento_id = dados_resultado.get("movimento_id")
        if dados_resultado.get("movimento_realizado") is True and movimento_id:
            produto = dados_resultado.get("produto")
            movimento = dados_resultado.get("movimento_tipo")
            quantidade = dados_resultado.get("quantidade_movimentada")
            memorias.append(
                self._salvar_memoria_automatica(
                    fase=3,
                    tipo="operacional",
                    chave=f"estoque-movimento-{movimento_id}",
                    valor=f"Estoque: {movimento} de {quantidade} em {produto}",
                    importancia=3,
                    metadados={"origem_resultado": "estoque"},
                )
            )

        return memorias

    def _aprender_uso(
        self,
        analise: dict[str, Any] | None,
        resultado: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not isinstance(analise, dict):
            return []

        intencao = analise.get("intencao")
        dominio = analise.get("dominio")
        if not intencao or not dominio:
            return []

        if resultado.get("agente") == "router":
            return []

        total = self.repository.contar_eventos(
            dominio=str(dominio),
            intencao=str(intencao),
        )
        if total < 3:
            return []

        memoria = self._salvar_memoria_automatica(
            fase=4,
            tipo="aprendizado_uso",
            chave=f"uso-{dominio}-{intencao}",
            valor=(
                f"Voce usa com frequencia a intencao {intencao} "
                f"na area {dominio}; registros: {total}"
            ),
            importancia=4,
            metadados={
                "dominio": dominio,
                "intencao": intencao,
                "total_eventos": total,
            },
        )
        return [memoria] if memoria else []

    def _aprender_estrategia(
        self,
        resultado: dict[str, Any],
    ) -> list[dict[str, Any]]:
        dados_resultado = self._dados_resultado(resultado)
        if not dados_resultado:
            return []

        memorias = []
        tipo_relatorio = dados_resultado.get("tipo_relatorio")
        tipo_resultado = dados_resultado.get("tipo_resultado")

        valor_a_receber = float(dados_resultado.get("valor_a_receber") or 0)
        if tipo_relatorio == "contas_resumo" and valor_a_receber > 0:
            memorias.append(
                self._salvar_memoria_automatica(
                    fase=5,
                    tipo="estrategica",
                    chave="estrategia-acompanhar-recebimentos",
                    valor=(
                        "Existe valor em aberto para receber: "
                        f"{self._moeda(valor_a_receber)}. "
                        "Acompanhar cobrancas e pagamentos parciais."
                    ),
                    importancia=5,
                    metadados={"valor_a_receber": valor_a_receber},
                )
            )

        valor_restante = float(dados_resultado.get("valor_restante") or 0)
        if tipo_resultado == "pedido" and valor_restante > 0:
            cliente = dados_resultado.get("cliente")
            pedido_id = dados_resultado.get("pedido_id")
            memorias.append(
                self._salvar_memoria_automatica(
                    fase=5,
                    tipo="estrategica",
                    chave=f"estrategia-pedido-{pedido_id}-receber",
                    valor=(
                        f"Pedido #{pedido_id} de {cliente} ainda tem "
                        f"{self._moeda(valor_restante)} para receber."
                    ),
                    importancia=5,
                    metadados={
                        "pedido_id": pedido_id,
                        "cliente": cliente,
                        "valor_restante": valor_restante,
                    },
                )
            )

        itens = dados_resultado.get("itens") or []
        if tipo_relatorio == "estoque_baixo" and itens:
            memorias.append(
                self._salvar_memoria_automatica(
                    fase=5,
                    tipo="estrategica",
                    chave="estrategia-estoque-baixo",
                    valor=(
                        "Ha produtos com estoque baixo. "
                        "Avaliar reposicao ou compra sob demanda."
                    ),
                    importancia=4,
                    metadados={"total_itens": len(itens)},
                )
            )

        return memorias

    def _salvar_memoria_automatica(
        self,
        fase: int,
        tipo: str,
        chave: str,
        valor: str,
        importancia: int,
        metadados: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        existente = self.repository.buscar_memoria_por_chave(chave)
        if existente:
            return self.repository.atualizar_memoria(
                memoria_id=int(existente["memoria_id"]),
                valor=valor,
                importancia=importancia,
                metadados=metadados or {},
            )

        return self.repository.registrar_memoria(
            fase=fase,
            tipo=tipo,
            chave=chave,
            valor=valor,
            origem="automatico",
            importancia=importancia,
            metadados=metadados or {},
        )

    def _dados_resultado(self, resultado: dict[str, Any]) -> dict[str, Any]:
        dados = resultado.get("dados")
        if not isinstance(dados, dict):
            return {}

        dados_resultado = dados.get("resultado")
        if isinstance(dados_resultado, dict):
            return dados_resultado

        return {}

    def _moeda(self, valor: Any) -> str:
        try:
            numero = float(valor or 0)
        except (TypeError, ValueError):
            numero = 0

        if numero.is_integer():
            return f"R$ {int(numero)}"

        return f"R$ {numero:.2f}"
