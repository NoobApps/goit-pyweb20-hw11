import random
from datetime import date, timedelta
import requests
from faker import Faker

# Ініціалізація Faker з українською локалізацією
fake = Faker("uk_UA")

# URL вашого REST API (змініть порт/хост за потреби)
BASE_URL = "http://localhost:8000/contacts/"

def generate_fake_contact():
    """Генерує випадкові дані для одного контакту."""
    # З генерацією випадкової дати народження (від 18 до 60 років)
    today = date.today()
    start_date = today - timedelta(days=365 * 60)
    end_date = today - timedelta(days=365 * 18)
    random_birthday = fake.date_between(start_date=start_date, end_date=end_date)

    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.unique.email(),
        "phone": fake.phone_number()[:20],  # Обрізаємо під обмеження Pydantic/БД (max 20 символів)
        "birthday": random_birthday.isoformat(),
        "additional_data": fake.sentence(nb_words=6) if random.choice([True, False]) else None
    }

def seed_database(count: int = 50):
    """Надсилає POST-запити до API для створення вказаної кількості контактів."""
    print(f"🚀 Починаємо заповнення бази даних ({count} контактів)...")
    
    successful_creates = 0

    for i in range(1, count + 1):
        payload = generate_fake_contact()
        try:
            response = requests.post(BASE_URL, json=payload, timeout=5)
            
            if response.status_code == 201:
                successful_creates += 1
                data = response.json()
                print(f"[{i}/{count}] ✅ Додано: {data['first_name']} {data['last_name']} (ID: {data['id']})")
            else:
                print(f"[{i}/{count}] ❌ Помилка {response.status_code}: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"[{i}/{count}] ⚠️ Помилка з'єднання з API: {e}")
            break

    print(f"\n🎉 Завершено! Успішно створено {successful_creates} з {count} контактів.")

if __name__ == "__main__":
    # Укажіть бажану кількість записів (наприклад, 50)
    seed_database(count=250)