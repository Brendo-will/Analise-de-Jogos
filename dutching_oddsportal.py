import asyncio
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from playwright.async_api import async_playwright


async def scroll_ate_carregar_todos(page, seletor="div.eventRow", tentativas_max_sem_novos=3):
    print("🔄 Iniciando scroll completo (topo e fim) até que nenhum novo jogo seja carregado...")

    jogos_renderizados = 0
    tentativas_sem_novos = 0

    while tentativas_sem_novos < tentativas_max_sem_novos:
        eventos = await page.query_selector_all(seletor)
        total_atual = len(eventos)

        if total_atual > jogos_renderizados:
            novos = total_atual - jogos_renderizados
            print(f"🆕 {novos} novos jogos encontrados. Total: {total_atual}")
            jogos_renderizados = total_atual
            tentativas_sem_novos = 0
        else:
            tentativas_sem_novos += 1
            print(f"⏳ Nenhum novo jogo. Tentativa {tentativas_sem_novos}/{tentativas_max_sem_novos}")

        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(1000)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)

    print(f"✅ Scroll finalizado. Total de jogos renderizados: {jogos_renderizados}")
    return await page.query_selector_all(seletor)


async def coletar_odds_via_dom(url):
    jogos = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print(f"🌐 Acessando: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

        try:
            await page.wait_for_selector("div.eventRow", timeout=20000)
        except:
            print("❌ Nenhum jogo encontrado.")
            await browser.close()
            return []

        events = await scroll_ate_carregar_todos(page, "div.eventRow")

        for event in events:
            try:
                teams = await event.query_selector_all(".participant-name")
                odds = await event.query_selector_all("p.height-content")
                hora_element = await event.query_selector("div.flex.w-full > p")

                if len(teams) == 2 and len(odds) >= 2:
                    texts = [await o.inner_text() for o in odds]
                    texts = [t.replace(",", ".").strip() for t in texts]

                    if any(t == "-" or not t for t in texts):
                        continue

                    team_1 = await teams[0].inner_text()
                    team_2 = await teams[1].inner_text()
                    hora = await hora_element.inner_text() if hora_element else "-"

                    try:
                        odd_1 = float(texts[0])
                        if len(texts) >= 3:
                            odd_x = float(texts[1])
                            odd_2 = float(texts[2])
                        else:
                            odd_x = None
                            odd_2 = float(texts[1])

                        prob_1 = round(100 / odd_1, 1)
                        prob_2 = round(100 / odd_2, 1)
                        gap_odds = round(abs(odd_1 - odd_2), 2)
                        soma_inv = (1 / odd_1) + (1 / odd_2) + (1 / odd_x) if odd_x else (1 / odd_1 + 1 / odd_2)
                        arbitragem = "Sim" if soma_inv < 1 else "Não"

                        odds_validas = [odd for odd in [odd_1, odd_2] if odd]
                        favorito = min(odds_validas)
                        zebra = max(odds_validas)

                        if favorito < 1.40 and zebra > favorito * 4:
                            acao = "BACK"
                            sugestao = "Apostar a favor do favorito (BACK)"
                        elif favorito < 1.30 and zebra > favorito * 5:
                            acao = "LAY"
                            sugestao = "Apostar contra o favorito (LAY)"
                        else:
                            acao = "NADA"
                            sugestao = "Analisar outros mercados, como gols"

                        if acao == "NADA":
                            if min(odd_1, odd_2) < 1.70:
                                prognostico = "Provável 1+ gol"
                                over_under = "Sugestão: Over 1.5"
                            elif all(o > 2.50 for o in [odd_1, odd_2]):
                                prognostico = "Jogo truncado (possível 0x0)"
                                over_under = "Sugestão: Under 1.5"
                            elif 1.8 <= odd_1 <= 2.2 and 1.8 <= odd_2 <= 2.2:
                                prognostico = "Mercado indefinido"
                                over_under = "Evitar aposta direta"
                            else:
                                prognostico = "Gols incertos"
                                over_under = "Avaliar estatísticas"
                        else:
                            prognostico = "-"
                            over_under = "-"

                        jogos.append({
                            "Horário": hora,
                            "Time 1": team_1,
                            "Time 2": team_2,
                            "Odd 1": odd_1,
                            "Odd X": odd_x,
                            "Odd 2": odd_2,
                            "% Chance Time 1": prob_1,
                            "% Chance Time 2": prob_2,
                            "Gap de Odds": gap_odds,
                            "Arbitragem?": arbitragem,
                            "Ação Recomendada": acao,
                            "O que fazer": sugestao,
                            "Prognóstico de Gols": prognostico,
                            "Over/Under 1.5": over_under,
                        })
                    except Exception as e:
                        print(f"Erro de processamento: {e}")
                        continue
            except Exception as e:
                print(f"Erro geral no evento: {e}")
                continue

        await browser.close()

    return jogos


def exportar_para_excel(jogos):
    if not jogos:
        print("⚠️ Nenhum jogo encontrado.")
        return

    df = pd.DataFrame(jogos)
    df = df.sort_values(by="Horário")
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

    print(f"✅ Exportado com sucesso para {arquivo_excel}")


if __name__ == "__main__":
    url = "https://www.oddsagora.com.br/matches/football/20250601/"
    jogos = asyncio.run(coletar_odds_via_dom(url))
    exportar_para_excel(jogos)
