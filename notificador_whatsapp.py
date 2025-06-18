import pandas as pd
from datetime import datetime, timedelta
import requests
import time
import json
import os

# Configurações do Telegram
TELEGRAM_TOKEN = 
CHAT_ID = 
ARQUIVO_ALERTADOS = "jogos_alertados.json"


def carregar_alertados():
    if os.path.exists(ARQUIVO_ALERTADOS):
        with open(ARQUIVO_ALERTADOS, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def salvar_alertados(alertados):
    with open(ARQUIVO_ALERTADOS, "w", encoding="utf-8") as f:
        json.dump(list(alertados), f, ensure_ascii=False, indent=2)


def enviar_telegram_alerta(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print("📨 Alerta enviado com sucesso ao Telegram.")
    else:
        print(f"❌ Erro ao enviar alerta: {response.text}")


def obter_ultimo_excel():
    arquivos = [f for f in os.listdir() if f.startswith('odds_') and f.endswith('.xlsx')]
    if not arquivos:
        return None
    return max(arquivos, key=os.path.getctime)


def verificar_alertas():
    EXCEL_PATH = obter_ultimo_excel()
    if not EXCEL_PATH:
        print("❌ Nenhum arquivo odds_ encontrado.")
        return

    df = pd.read_excel(EXCEL_PATH)
    agora = datetime.now()
    hoje = agora.date()
    alertados = carregar_alertados()
    novos_alertas = set()

    for _, row in df.iterrows():
        hora_jogo_str = str(row['Horário']).strip().replace("'", "").replace('"', '').replace("’", "")

        if any(x in hora_jogo_str for x in ["+", "HT", "FT", "ET"]) or not hora_jogo_str.replace(":", "").isdigit():
            with open("horarios_invalidos.txt", "a", encoding="utf-8") as log:
                log.write(f"Ignorado (não reconhecido): {hora_jogo_str}\n")
            continue

        if ":" not in hora_jogo_str:
            hora_jogo_str = hora_jogo_str.zfill(2) + ":00"

        try:
            partes = hora_jogo_str.split(":")
            hora_int = int(partes[0])
            minuto_int = int(partes[1])

            if hora_int > 23 or minuto_int > 59:
                with open("horarios_invalidos.txt", "a", encoding="utf-8") as log:
                    log.write(f"Ignorado (fora de range): {hora_jogo_str}\n")
                continue

            hora_jogo = datetime.strptime(hora_jogo_str, "%H:%M")
            hora_jogo = hora_jogo.replace(year=hoje.year, month=hoje.month, day=hoje.day)
            hora_alerta = hora_jogo + timedelta(minutes=15)

            identificador = f"{hora_jogo.strftime('%H:%M')}|{row['Time 1']} x {row['Time 2']}"
            if identificador in alertados:
                continue

            acao = row.get('Ação Recomendada', '').strip()
            arbitragem = row.get('Arbitragem?', 'Não').strip()

            if acao == 'NADA' and arbitragem != 'Sim':
                continue

            if timedelta(seconds=0) <= agora - hora_alerta <= timedelta(minutes=1):
                mensagem = f"""
⏰ *Alerta 15 minutos após o início do jogo!*

⚽ *{row['Time 1']}* x *{row['Time 2']}*
🕒 *Início:* `{hora_jogo.strftime('%H:%M')}`
🕒 *Alerta:* `{hora_alerta.strftime('%H:%M')}`

💰 *Odds*:
• {row['Time 1']}: `{row.get('Odd 1', '-')}` ({row.get('% Chance Time 1', '-')}%)
• Empate: `{row.get('Odd X', '-')}`
• {row['Time 2']}: `{row.get('Odd 2', '-')}` ({row.get('% Chance Time 2', '-')}%)

📊 *Ação*: {acao}
🎯 *Prognóstico*: {row.get('Prognóstico de Gols', '-')}
⚖️ *Arbitragem?* {arbitragem}
📉 *Gap de Odds*: {row.get('Gap de Odds', '-')}
"""
                enviar_telegram_alerta(mensagem.strip())
                novos_alertas.add(identificador)

        except Exception as e:
            print(f"⚠️ Erro ao processar horário '{hora_jogo_str}': {e}")
            with open("horarios_invalidos.txt", "a", encoding="utf-8") as log:
                log.write(f"Erro de parsing: {hora_jogo_str} → {e}\n")

    if novos_alertas:
        alertados.update(novos_alertas)
        salvar_alertados(alertados)


# Execução contínua
if __name__ == "__main__":
    while True:
        print(f"🔍 Verificando alertas... {datetime.now().strftime('%H:%M:%S')}")
        verificar_alertas()
        time.sleep(20)
