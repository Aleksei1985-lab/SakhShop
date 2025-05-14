import smtplib
from email.mime.text import MIMEText
from config import settings

msg = MIMEText("Тестовое сообщение")
msg["Subject"] = "Тест SMTP"
msg["From"] = settings.SMTP_USER
msg["To"] = "aleksey.oberemok@yandex.ru"  # Замени на свой email для теста

try:
    with smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
        server.set_debuglevel(1)  # Включаем отладку для диагностики
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
    print("Email успешно отправлен")
except Exception as e:
    print(f"Ошибка: {str(e)}")
