import random
import time
import string
from database import DB
from common.models import User, Geo, Filters, Gender, FType, Hobby, Orientation, Role


def random_str(length=6):
    return ''.join(random.choices(string.ascii_letters, k=length))


def random_geo():
    cities = [
        ("Украина", "UA", "Киев"),
        ("Украина", "UA", "Львов"),
        ("Украина", "UA", "Одесса"),
        ("Казахстан", "KZ", "Алмата"),
        ("Россия", "RU", "Москва"),
        ("Грузия", "GE", "Тбилиси")
    ]
    country, code, city = random.choice(cities)
    return Geo(country=country, country_code=code, city=city)


def random_filters():
    geo_ = random_geo()
    return Filters(
        geo=geo_,
        age_from=random.randint(9, 22),
        age_to=random.randint(16, 30),
        sex=[random.choice(list(Gender))],
        ftype=[random.choice([FType.basic, FType.romantic])],
        hobby=random.sample(list(Hobby), k=random.randint(1, 3))
    )


if __name__ == "__main__":
    db = DB.get()
    print("🧼 очищаем таблицу users...")
    db.execute("DELETE FROM users")

    print("📥 добавляем анкеты...\n")
    for i in range(50):
        tg_id = random.randint(100000, 99999999)
        name = random_str(8).capitalize()
        geo = random_geo()
        filters = random_filters()
        age = random.randint(9, 30)
        sex = random.choice(list(Gender))
        hobby = random.sample(list(Hobby), k=random.randint(1, 3))
        bio = "я просто тестовый юзер 👻"
        orientation = random.choice(list(Orientation))
        media = []
        registered_at = int(time.time())

        try:
            User.create(
                tg_id=tg_id,
                role=Role.user,
                name=name,
                geo=geo.model_dump(),
                filters=filters.model_dump(),
                age=age,
                sex=sex,
                hobby=hobby,
                bio=bio,
                orientation=orientation,
                media=media,
                registered_at=registered_at
            )
            print(f"✅ [{i+1}/100] {name}, {age} лет, {sex.value}, г. {geo.city}, {geo.country}")
        except Exception as e:
            print(f"⚠️ ошибка на {i}: {e}")

    print("\n🎉 50 анкет добавлены!")
