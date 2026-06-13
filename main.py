"""
Ponto de entrada simples do Cooper.

Este arquivo monta o Cooper com seus agentes principais, interpretador NLP,
roteador e construtor de respostas. A CLI local serve como bancada de testes
para evoluir agentes, intencoes e respostas.
"""

from agents.compras_agent import ComprasAgent
from agents.contas_agent import ContasAgent
from agents.agenda_agent import AgendaAgent
from agents.backup_agent import BackupAgent
from agents.busca_agent import BuscaAgent
from agents.clientes_agent import ClientesAgent
from agents.estoque_agent import EstoqueAgent
from agents.fornecedores_agent import FornecedoresAgent
from agents.memoria_agent import MemoriaAgent
from agents.pedidos_agent import PedidosAgent
from agents.precificacao_agent import PrecificacaoAgent
from agents.relatorios_agent import RelatoriosAgent
from agents.vendas_agent import VendasAgent
from core.cooper import Cooper
from core.response_builder import ResponseBuilder
from core.router import Router
from nlp.interpretador import Interpretador
from repositories.backup_repository import BackupRepository
from repositories.clientes_repository import ClientesRepository
from repositories.contas_repository import ContasRepository
from repositories.estoque_repository import EstoqueRepository
from repositories.fornecedores_repository import FornecedoresRepository
from repositories.memoria_repository import MemoriaRepository
from repositories.pedidos_repository import PedidosRepository
from repositories.vendas_repository import VendasRepository


COMANDOS_SAIDA = {"sair", "exit", "quit"}
PREFIXOS_RESPOSTA = {
    "operacao:",
    "registro de",
    "produto:",
    "variacao:",
    "saldo atual:",
    "entrada registrada:",
    "saida registrada:",
    "sku:",
    "inventario:",
}


def criar_cooper() -> Cooper:
    """
    Cria uma instancia padrao do Cooper com os agentes principais.

    Returns:
        Instancia configurada do Cooper.
    """
    estoque_repository = EstoqueRepository()
    vendas_repository = VendasRepository()
    pedidos_repository = PedidosRepository()
    contas_repository = ContasRepository()
    clientes_repository = ClientesRepository()
    fornecedores_repository = FornecedoresRepository()
    memoria_repository = MemoriaRepository()
    backup_repository = BackupRepository()
    memoria_agent = MemoriaAgent(
        repository=memoria_repository,
    )

    router = Router(
        agents=[
            memoria_agent,
            AgendaAgent(
                pedidos_repository=pedidos_repository,
                contas_repository=contas_repository,
            ),
            BackupAgent(
                repository=backup_repository,
            ),
            BuscaAgent(
                clientes_repository=clientes_repository,
                pedidos_repository=pedidos_repository,
                fornecedores_repository=fornecedores_repository,
                estoque_repository=estoque_repository,
            ),
            FornecedoresAgent(
                repository=fornecedores_repository,
            ),
            ClientesAgent(
                repository=clientes_repository,
            ),
            PedidosAgent(
                repository=pedidos_repository,
                contas_repository=contas_repository,
            ),
            ContasAgent(
                pedidos_repository=pedidos_repository,
                contas_repository=contas_repository,
            ),
            RelatoriosAgent(
                estoque_repository=estoque_repository,
                vendas_repository=vendas_repository,
                pedidos_repository=pedidos_repository,
            ),
            PrecificacaoAgent(),
            VendasAgent(
                estoque_repository=estoque_repository,
                vendas_repository=vendas_repository,
            ),
            ComprasAgent(),
            EstoqueAgent(repository=estoque_repository),
        ]
    )

    return Cooper(
        router=router,
        response_builder=ResponseBuilder(),
        interpretador=Interpretador(),
        memoria_repository=memoria_repository,
        memoria_agent=memoria_agent,
    )


def exibir_ajuda() -> None:
    """Mostra os comandos disponiveis na interface local."""
    print("Comandos:")
    print("  ajuda        Mostra esta ajuda.")
    print("  exemplos     Mostra frases de teste.")
    print("  agentes      Lista os agentes carregados.")
    print("  debug        Liga ou desliga a resposta tecnica.")
    print("  sair         Encerra o Cooper.")


def exibir_exemplos() -> None:
    """Mostra exemplos de mensagens para testar o Cooper."""
    print("Exemplos:")
    print("  entrada de 12 produto camiseta preta m")
    print("  consultar saldo do produto camiseta preta m")
    print("  saida de 2 produto camiseta preta m")
    print("  entrada de 4 produto camiseta preta g")
    print("  inventario estoque")
    print("  quanto vendi hoje?")
    print("  produtos com estoque baixo")
    print("  historico da camiseta preta m")
    print("  cadastre cliente Maria telefone 11999999999")
    print("  endereco da Maria e rua das flores 123")
    print("  anota no cliente Maria que prefere pagar no pix")
    print("  dados da Maria")
    print("  listar clientes")
    print("  cadastre fornecedor Moda Bella telefone 11988887777")
    print("  fornecedor Moda Bella vende calcinha preta fio duplo g por 10")
    print("  anota no fornecedor Moda Bella que entrega rapido")
    print("  dados do fornecedor Moda Bella")
    print("  fornecedores da calcinha preta")
    print("  listar fornecedores")
    print("  buscar Maria")
    print("  procura calcinha preta")
    print("  encontrar pedido 1")
    print("  buscar fornecedor Moda Bella")
    print("  cliente Maria pediu uma camiseta preta m por 80")
    print("  confirmei pedido da Maria")
    print("  comprei a camiseta da Maria por 45")
    print("  Maria pagou 40")
    print("  quanto Maria deve?")
    print("  altera valor do pedido da Maria para 90")
    print("  troca tamanho do pedido da Maria para g")
    print("  cancela pedido da Maria")
    print("  cancela pedido 1")
    print("  cancelar #1")
    print("  historico do pedido da Maria")
    print("  historico do pedido 1")
    print("  comprei pedido 1 por 45")
    print("  Maria pagou 40 pelo pedido 1")
    print("  marcar pedido 1 como entregue")
    print("  entreguei pedido da Maria")
    print("  concluir pedido da Maria")
    print("  concluir pedido 1")
    print("  quais pedidos pendentes?")
    print("  pedidos concluidos")
    print("  quanto tenho pra receber?")
    print("  contador")
    print("  qual meu lucro?")
    print("  gastei 20 com embalagem")
    print("  paguei motoboy 15")
    print("  entrou 100 no caixa")
    print("  saiu 10 do caixa para gasolina")
    print("  quanto tem no caixa?")
    print("  despesas")
    print("  comprei uma calca no valor de 100")
    print("  lembre que eu normalmente dobro o valor da peca")
    print("  o que voce lembra?")
    print("  memoria operacional")
    print("  aprendizados")
    print("  memoria estrategica")
    print("  historico de conversa")
    print("  o que preciso fazer hoje?")
    print("  agenda da loja")
    print("  prioridades de hoje")
    print("  fazer backup")
    print("  exportar dados")
    print("  exportar planilha")
    print("  listar backups")


def parece_resposta_colada(msg: str) -> bool:
    """Indica se o usuario colou uma resposta do Cooper como entrada."""
    texto = (msg or "").strip().lower()
    return any(texto.startswith(prefixo) for prefixo in PREFIXOS_RESPOSTA)


def main() -> None:
    """Executa uma interface de linha de comando simples para testes locais."""
    cooper = criar_cooper()
    debug = False

    print("Cooper iniciado. Digite 'sair' para encerrar.")
    print("Digite 'ajuda' para ver os comandos disponiveis.")

    while True:
        msg = input("Voce: ").strip()
        comando = msg.lower()

        if comando in COMANDOS_SAIDA:
            print("Cooper encerrado.")
            break

        if not msg:
            print("Cooper: Envie uma mensagem para eu analisar.")
            continue

        if parece_resposta_colada(msg):
            print(
                "Cooper: Parece que voce colou uma resposta minha. "
                "Digite uma solicitacao, por exemplo: "
                "'entrada de 12 produto camiseta preta m'."
            )
            continue

        if comando in {"ajuda", "help", "?"}:
            exibir_ajuda()
            continue

        if comando in {"exemplos", "exemplo"}:
            exibir_exemplos()
            continue

        if comando == "agentes":
            nomes = ", ".join(cooper.listar_agents())
            print(f"Cooper: Agentes carregados: {nomes}.")
            continue

        if comando == "debug":
            debug = not debug
            estado = "ligado" if debug else "desligado"
            print(f"Cooper: Modo debug {estado}.")
            continue

        resultado = cooper.processar(msg)
        if debug:
            resposta = cooper.response_builder.construir_debug(resultado)
        else:
            resposta = cooper.response_builder.construir(resultado)

        print(f"Cooper: {resposta}")


if __name__ == "__main__":
    main()
