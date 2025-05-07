import pandas as pd
from datetime import datetime, timedelta, date
import pywhatkit
import os

# ====== CONFIGURAÇÕES ======
NUMERO_DESTINO = "+5511949443193"  # Seu número com DDI
PASTA_EXCEL = "."                 # Onde estão os arquivos
LOG_ARQUIVO = "jogos_enviados.txt"

def encontrar_arquivo_do_dia():
    hoje = date.today().strftime("%Y-%m-%d")
    arquivos = [f for f in os.listdir(PASTA_EXCEL) if f.startswith(f"odds_{hoje}") and f.endswith(".xlsx")]
    return max(arquivos, key=os.path.getctime) if arquivos else None

def enviar_alertas():
    ARQUIVO_EXCEL = encontrar_arquivo_do_dia()
    if not ARQUIVO_EXCEL:
        print("⚠️ Nenhum arquivo odds_ encontrado para hoje.")
        return

    print(f"📂 Usando arquivo: {ARQUIVO_EXCEL}")
    df = pd.read_excel(ARQUIVO_EXCEL)
    agora = datetime.now()

    # Carregar jogos já enviados
    enviados = set()
    if os.path.exists(LOG_ARQUIVO):
        with open(LOG_ARQUIVO, "r") as f:
            enviados = set(f.read().splitlines())

    for _, row in df.iterrows():
        try:
            horario_jogo_str = str(row["Horário"]).strip()
            if ":" not in horario_jogo_str:
                continue

            hora_jogo = datetime.strptime(horario_jogo_str, "%H:%M")

            # Corrigir para jogos na madrugada
            if hora_jogo.hour < 3 and agora.hour > 20:
                hora_jogo = hora_jogo.replace(day=agora.day + 1)
            else:
                hora_jogo = hora_jogo.replace(day=agora.day)

            hora_jogo = hora_jogo.replace(year=agora.year, month=agora.month)

            # Evitar mensagens duplicadas
            id_jogo = f"{row['Time 1']} x {row['Time 2']} {row['Horário']}"
            if id_jogo in enviados:
                continue

            # Se o jogo estiver entre agora e os próximos 10 minutos
            if timedelta(minutes=0) <= (hora_jogo - agora) <= timedelta(minutes=10):
                msg = f"🔔 Jogo em breve ({row['Horário']}):\n⚽ {row['Time 1']} x {row['Time 2']}\n🎯 Ação: {row['Ação Recomendada']}\n💡 {row['O que fazer']}"
                if 'Link do Jogo' in row and isinstance(row['Link do Jogo'], str):
                    msg += f"\n🔗 {row['Link do Jogo']}"
                pywhatkit.sendwhatmsg_instantly(NUMERO_DESTINO, msg, wait_time=10)
                print(f"✅ Mensagem enviada para: {id_jogo}")

                with open(LOG_ARQUIVO, "a") as f:
                    f.write(id_jogo + "\n")

        except Exception as e:
            print(f"❌ Erro ao processar jogo: {e}")

if __name__ == "__main__":
    enviar_alertas()
