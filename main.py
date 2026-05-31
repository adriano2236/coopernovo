from core.cooper import Cooper
from config import NOME_IA, VERSAO

print(f"\n🤖 {NOME_IA} | Versão {VERSAO}")
print("Gerente de Loja\n")

cooper = Cooper()

while True:
    msg = input("Você: ")
    if msg.lower() in ["sair", "tchau"]:
        print("Cooper: Até logo!")
        break
    resp = cooper.processar(msg)
    print(f"Cooper: {resp}\n")