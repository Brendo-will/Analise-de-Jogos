from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo


def coletar_odds_oddsportal(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    jogos = []

    try:
        driver.get(url)
        time.sleep(3)

        previous_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == previous_height:
                break
            previous_height = new_height

        games = driver.find_elements(By.CSS_SELECTOR, "div.eventRow")
        print(f"Total de jogos encontrados: {len(games)}")

        for event in games:
            try:
                teams = event.find_elements(By.CSS_SELECTOR, ".participant-name")
                odds = event.find_elements(By.CSS_SELECTOR, "p.height-content")
                link_element = event.find_element(By.CSS_SELECTOR, "a[href]")
                link_jogo = link_element.get_attribute("href")
                try:
                    hora_element = event.find_element(By.CSS_SELECTOR, "div.flex.w-full > p")
                    hora = hora_element.text.strip()
                except:
                    hora = "-"



                if len(teams) == 2 and len(odds) >= 2:
                    texts = [o.text.replace(',', '.') for o in odds]
                    if any(t.strip() == '-' or not t.strip() for t in texts):
                        print("❌ Odds inválidas, pulando jogo:", texts)
                        continue

                    try:
                        team_1 = teams[0].text
                        team_2 = teams[1].text

                        odd_1 = float(texts[0])

                        if len(texts) >= 3:
                            odd_x = float(texts[1])
                            odd_2 = float(texts[2])
                        else:
                            odd_x = None
                            odd_2 = float(texts[1])

                        odds_validas = [odd for odd in [odd_1, odd_2] if odd is not None]
                        favorito = min(odds_validas)
                        zebra = max(odds_validas)

                        if favorito < 1.40 and zebra > 6.0:
                            acao = "BACK"
                            sugestao = "Apostar a favor do favorito (BACK)"
                        elif favorito < 1.30 and zebra > 7.5:
                            acao = "LAY"
                            sugestao = "Apostar contra o favorito (LAY)"
                        else:
                            acao = "NADA"
                            sugestao = "Analisar outros mercados, como gols"

                        # Prognóstico de gols baseado nas odds
                        if acao == "NADA":
                            if min(odd_1, odd_2) < 1.70:
                                prognostico = "Provável 1+ gol"
                                over_under = "Sugestão: Over 1.5"
                            elif all(o > 2.50 for o in [odd_1, odd_2]):
                                prognostico = "Jogo truncado (possível 0x0)"
                                over_under = "Sugestão: Under 1.5"
                            else:
                                prognostico = "Gols incertos"
                                over_under = "Sugestão: Avaliar estatísticas"
                        else:
                            prognostico = "-"
                            over_under = "-"

                        # Simular estatísticas básicas (fictícias por enquanto)
                        confrontos_diretos = "Time 1 venceu 3 dos últimos 5 confrontos"
                        ultimos_jogos_time_1 = "Time 1: 2V 1E 2D"
                        ultimos_jogos_time_2 = "Time 2: 3V 0E 2D"

                        jogos.append({
                            "Horário": hora,
                            "Time 1": team_1,
                            "Time 2": team_2,
                            "Odd 1": odd_1,
                            "Odd X": odd_x,
                            "Odd 2": odd_2,
                            "Ação Recomendada": acao,
                            "O que fazer": sugestao,
                            "Prognóstico de Gols": prognostico,
                            "Over/Under 1.5": over_under,
                           
                        })
                    except ValueError:
                        print("❌ Erro ao converter odds em float:", texts)
                        continue
            except Exception as e:
                pass

    finally:
        driver.quit()

    if jogos:
        df = pd.DataFrame(jogos)
        data_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        arquivo_excel = f"odds_{data_str}.xlsx"
        df.to_excel(arquivo_excel, index=False)

        wb = load_workbook(arquivo_excel)
        ws = wb.active
        tab = Table(displayName="OddsTable", ref=ws.dimensions)
        style = TableStyleInfo(name="TableStyleMedium9", showFirstColumn=False,
                               showLastColumn=False, showRowStripes=True, showColumnStripes=False)
        tab.tableStyleInfo = style
        ws.add_table(tab)
        wb.save(arquivo_excel)

        print(f"📁 Resultados exportados para {arquivo_excel} com filtros automáticos.")

    return jogos
