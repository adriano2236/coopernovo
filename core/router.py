"""
Roteador central do Cooper.

Este módulo define a classe Router, responsável por escolher qual agente deve
processar uma mensagem recebida. O Router não executa regra de negócio própria,
não formata respostas finais e não conversa diretamente com o usuário.

Regra arquitetural principal:
    Router = seleção e delegação

A responsabilidade do Router é percorrer os agentes registrados, identificar o
primeiro agente capaz de processar a mensagem e delegar o processamento a ele.

Além disso, mantém funcionalidades importantes da versão original:
- Tratamento de saudações e despedidas
- Acesso ao contexto, eventos e tarefas
- Lógica de fallback inteligente
"""

from typing import Any, Optional, List


class Router:
    """
    Coordena a escolha do agente apropriado para uma mensagem.

    O Router recebe uma lista de agentes especializados e consulta cada um por
    meio do método `pode_processar`. Quando encontra um agente compatível,
    chama o método `processar` desse agente e retorna o dicionário produzido.

    Herda estrutura da versão nova e funcionalidades da versão original.
    """

    def __init__(self, actions: Any = None, contexto: Any = None, 
                 tasks: Any = None, event_bus: Any = None) -> None:
        """
        Inicializa o roteador com dependências e registra os agentes padrão.

        Args:
            actions: Ações globais do sistema (herdado do original)
            contexto: Gerenciador de contexto e NLP (herdado do original)
            tasks: Gerenciador de tarefas (herdado do original)
            event_bus: Barramento de eventos para comunicação (herdado do original)
        """
        # Dependências do sistema (mantidas do original)
        self.actions = actions
        self.contexto = contexto
        self.tasks = tasks
        self.event_bus = event_bus

        # Rotas diretas (mantido do original)
        self.routes: dict = {}

        # Lista de agentes (estrutura nova + instâncias do original)
        self.agents: List[Any] = []  # Any = BaseAgent, mas evitamos import circular

        # Registrar agentes padrão
        self._registrar_agentes_padrao()

    def _registrar_agentes_padrao(self) -> None:
        """
        Instancia e registra os agentes padrão do sistema,
        mantendo as dependências de cada um como na versão original.
        """
        from agents.compras_agent import ComprasAgent
        from agents.vendas_agent import VendasAgent
        from agents.estoque_agent import EstoqueAgent
        from agents.resumo_agent import ResumoAgent
        from agents.atualizar_agent import AtualizarAgent
        
        self.registrar(ComprasAgent(self.event_bus))
        self.registrar(VendasAgent(self.event_bus))
        self.registrar(EstoqueAgent())
        self.registrar(ResumoAgent())
        self.registrar(AtualizarAgent())

    def registrar(self, agent: Any) -> None:
        """
        Registra um novo agente no roteador.

        Args:
            agent: Instância de um agente que herda de BaseAgent.
        """
        # Verificação opcional - pode remover se causar problemas
        # if not hasattr(agent, 'pode_processar') or not hasattr(agent, 'processar'):
        #     raise TypeError("O agente deve ter métodos pode_processar e processar")
        
        self.agents.append(agent)

    def processar(self, msg: str) -> dict[str, Any]:
        """
        Método principal de processamento (mesmo nome do original, arquitetura nova).
        Fluxo completo: tratamento simples → análise → roteamento → fallback.

        Args:
            msg: Mensagem original enviada ao Cooper.

        Returns:
            Dicionário padronizado com o resultado do processamento.
        """
        mensagem = (msg or "").strip()

        if not mensagem:
            return self._resposta_fallback(
                status="erro",
                tipo="Mensagem_vazia",
                erro="mensagem_vazia",
            )

        # 1. Tratamento direto: Saudações e Despedidas (mantido do original)
        tratamento_direto = self._verificar_mensagens_simples(mensagem)
        if tratamento_direto:
            return tratamento_direto

        # 2. Rotas diretas (mantido do original)
        if mensagem.lower() in self.routes:
            return self.routes[mensagem.lower()]()

        # 3. Análise NLP e Contexto (lógica do original adaptada)
        analise = self._realizar_analise(mensagem)

        # 4. Roteamento por agente (lógica nova: usa pode_processar)
        for agente in self.agents:
            if agente.pode_processar(mensagem):
                resposta = agente.processar(mensagem, analise=analise)

                # Registrar no contexto (mantido do original)
                if self.contexto and hasattr(self.contexto, 'registrar'):
                    self.contexto.registrar(mensagem, resposta, analise)

                return {
                    "agente": agente.nome,
                    "resposta": resposta,
                    "analise": analise
                }

        # 5. Fallback inteligente (lógica do original adaptada ao padrão dict)
        return self._resposta_fallback(
            status="erro",
            tipo="agente_nao_encontrado",
            dados={"sugestoes": self._fallback_original(mensagem)},
            erro="agente_nao_encontrado"
        )

    def _verificar_mensagens_simples(self, msg: str) -> Optional[dict[str, Any]]:
        """
        Verifica saudações e despedidas, retorna resposta padronizada.
        """
        msg_lower = msg.lower()

        saudacoes = ["oi", "ola", "olá", "bom dia", "boa tarde", "boa noite"]
        despedidas = ["tchau", "sair", "fim", "encerrar", "desligar"]

        if msg_lower in saudacoes:
            return {
                "agente": "router",
                "status": "ok",
                "tipo": "saudacao",
                "dados": {},
                "erro": None
            }

        if msg_lower in despedidas:
            return {
                "agente": "router",
                "status": "ok",
                "tipo": "despedida",
                "dados": {},
                "erro": None
            }

        return None

    def _realizar_analise(self, msg: str) -> dict[str, Any]:
        """
        Executa a análise NLP com a lógica de contexto do projeto original.
        """
        if not self.contexto:
            return {"intencao": "desconhecido", "entidades": {}}

        analise = self.contexto.analisar(msg)

        # Lógica de correção de intenção do original
        if (analise.get("intencao") == "desconhecido" 
            and analise.get("entidades", {}).get("referencia")):
            
            ultima_intencao = None
            if hasattr(self.contexto, 'contexto'):
                ultima_intencao = self.contexto.contexto.get("estado_atual", {}).get("ultima_intencao")
            
            if ultima_intencao:
                analise["intencao"] = ultima_intencao

        return analise

    def _fallback_original(self, msg: str) -> str:
        """
        Mantém a lógica de ajuda/sugestão do arquivo original,
        retorna o texto como dado para ser usado pelo ResponseBuilder.
        """
        msg = msg.lower()

        if any(p in msg for p in ["vendi", "vende", "venda"]):
            return "Entendi que você quer registrar uma venda. Exemplo: vendi 2 calcinha codigo 720 por 25 reais"

        if any(p in msg for p in ["comprei", "compra", "comprar"]):
            return "Entendi que você quer registrar uma compra. Exemplo: comprei 5 calcinha codigo 720 por 10 reais"

        if any(p in msg for p in ["estoque", "produto", "codigo"]):
            return "Você pode consultar o estoque dizendo: estoque"

        return (
            "Não entendi o comando.\n"
            "Exemplos:\n"
            "- comprei 5 calcinha codigo 720 por 10 reais\n"
            "- vendi 2 calcinha codigo 720 por 25 reais\n"
            "- estoque\n"
            "- resumo"
        )

    def listar_agents(self) -> List[str]:
        """Lista os nomes dos agentes registrados."""
        return [agente.nome for agente in self.agents if hasattr(agente, 'nome')]

    def _resposta_fallback(
        self,
        status: str,
        tipo: str,
        dados: Optional[dict[str, Any]] = None,
        erro: Optional[str] = None,
    ) -> dict[str, Any]:
        """Formato padrão de resposta para erros ou não processamento."""
        return {
            "agente": "router",
            "status": status,
            "tipo": tipo,
            "dados": dados or {},
            "erro": erro,
        }

    def __repr__(self) -> str:
        """Representação para depuração."""
        return f"Router(agents={self.listar_agents()!r})"