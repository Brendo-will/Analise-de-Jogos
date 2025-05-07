import schedule
import time
from notificador_whatsapp import enviar_alertas

schedule.every(10).minutes.do(enviar_alertas)

print("🔄 Monitoramento iniciado... Enviando alertas a cada 10 minutos.")

while True:
    schedule.run_pending()
    time.sleep(60)
