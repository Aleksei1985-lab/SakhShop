# Создаем новый файл gosuslugi.py
import requests
from fastapi import HTTPException

GOSUSLUGI_API = "https://api.gosuslugi.ru/"

async def verify_user(passport_data: dict):
    try:
        response = requests.post(
            f"{GOSUSLUGI_API}/verify",
            json=passport_data,
            headers={"Authorization": f"Bearer {os.getenv('GOSUSLUGI_TOKEN')}"}
        )
        return response.json().get("verified", False)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Ошибка верификации")