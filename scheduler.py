from dutching_oddsportal import coletar_odds_oddsportal
import time
from datetime import datetime
from datetime import datetime, timedelta
import schedule
import time




def escolher_url():
    print("\nQual data você quer analisar?")
    print("1. Jogos de HOJE")
    print("2. Jogos de AMANHÃ")
    dia = input("Escolha: ")

    if dia == "1":
        data = datetime.now()
    elif dia == "2":
        data = datetime.now() + timedelta(days=1)
    else:
        print("Opção inválida. Usando HOJE por padrão.")
        data = datetime.now()

    data_formatada = data.strftime("%Y%m%d")

    print("\nQual esporte você quer analisar?")
    print("1. Futebol")
    print("2. Basquete")
    esporte = input("Escolha: ")

    if esporte == "1":
        return f"https://www.oddsagora.com.br/matches/football/{data_formatada}/"
    elif esporte == "2":
        return f"https://www.oddsagora.com.br/matches/basketball/{data_formatada}/"
    else:
        print("Opção inválida. Usando Futebol por padrão.")
        return f"https://www.oddsagora.com.br/matches/football/{data_formatada}/"
def listar_jogos_lucrativos(url):
    investimento = float(input("Valor total para investir (ex: 100): "))
    jogos = coletar_odds_oddsportal(url)
    encontrados = 0

    print("\n💸 JOGOS COM LUCRO POSITIVO:\n")

    for jogo in jogos:
        odds = [jogo["Odd 1"], jogo["Odd X"], jogo["Odd 2"]]
        if all(o > 1 for o in odds):
            soma_inversos = sum(1 / o for o in odds)
            if soma_inversos < 1:
                stakes = [(investimento / o) / soma_inversos for o in odds]
                retorno = stakes[0] * odds[0]
                lucro = retorno - investimento

                print(f"{jogo['Time 1']} x {jogo['Time 2']}")
                print(f"Odds: 1={odds[0]} | X={odds[1]} | 2={odds[2]}")
                print(f"Lucro estimado: R${round(lucro, 2)}\n")
                encontrados += 1

    if encontrados == 0:
        print("Nenhum jogo com lucro positivo encontrado.")
    else:
        print(f"✅ Total de jogos lucrativos: {encontrados}\n")


def listar_jogos_back_lay(url):
    jogos = coletar_odds_oddsportal(url)
    back_favoritos = []
    lay_favoritos = []

    for jogo in jogos:
        try:
            o1, ox, o2 = jogo["Odd 1"], jogo["Odd X"], jogo["Odd 2"]
            odds = [o1, ox, o2]
            favorito = min(odds)
            zebra = max(odds)

            if favorito < 1.40 and zebra > 6.0:
                back_favoritos.append((jogo['Time 1'], jogo['Time 2'], odds))

            if favorito < 1.30 and zebra > 7.5:
                lay_favoritos.append((jogo['Time 1'], jogo['Time 2'], odds))
        except:
            continue

    print("\n🎯 JOGOS BONS PARA BACK:\n")
    for t1, t2, odds in back_favoritos:
        print(f"{t1} x {t2} | Odds: 1={odds[0]} | X={odds[1]} | 2={odds[2]}")

    print("\n🚫 JOGOS BONS PARA LAY NO FAVORITO:\n")
    for t1, t2, odds in lay_favoritos:
        print(f"{t1} x {t2} | Odds: 1={odds[0]} | X={odds[1]} | 2={odds[2]}")

    print(f"\nTotal BACK: {len(back_favoritos)} | Total LAY: {len(lay_favoritos)}\n")


def calcular_dutching(url):
    time_1 = input("Digite o nome do primeiro time: ").strip().lower()
    time_2 = input("Digite o nome do segundo time: ").strip().lower()
    investimento = float(input("Valor total para investir (ex: 100): "))

    jogos = coletar_odds_oddsportal(url)

    for jogo in jogos:
        if time_1 in jogo["Time 1"].lower() and time_2 in jogo["Time 2"].lower():
            odds = [jogo["Odd 1"], jogo["Odd X"], jogo["Odd 2"]]
            soma_inversos = sum(1 / o for o in odds)
            stakes = [(investimento / o) / soma_inversos for o in odds]
            retorno = stakes[0] * odds[0]
            lucro = retorno - investimento

            print(f"\n🎯 Jogo encontrado: {jogo['Time 1']} x {jogo['Time 2']}")
            print(f"Odds: 1={odds[0]} | X={odds[1]} | 2={odds[2]}")
            print(f"Stakes: {[round(s, 2) for s in stakes]}")
            print(f"Retorno esperado: R${round(retorno, 2)}")
            print(f"Lucro estimado: R${round(lucro, 2)}\n")
            return

    print("❌ Jogo não encontrado.")


def sair():
    print("Encerrando... 👋")
    time.sleep(1)
    exit()


def menu():
    while True:
        print("\n======= MENU DUTCHING =======")
        print("1. Listar todos os jogos com lucro positivo")
        print("2. Sugerir jogos para BACK ou LAY")
        print("3. Calcular dutching para um jogo específico")
        print("4. Sair")
        escolha = input("Escolha uma opção: ")

        if escolha == "1":
            url = escolher_url()
            listar_jogos_lucrativos(url)
        elif escolha == "2":
            url = escolher_url()
            listar_jogos_back_lay(url)
        elif escolha == "3":
            url = escolher_url()
            calcular_dutching(url)
        elif escolha == "4":
            sair()
        else:
            print("Opção inválida. Tente novamente.")


if __name__ == "__main__":
    menu()
