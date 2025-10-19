import time
import json
import random
from enum import Enum
from typing import Optional, List, Self
from pydantic import BaseModel

from config import DEBUG
from database import DB


# --- ENUM'Ы --- #
class Gender(str, Enum):
    male = "Мужской"
    female = "Женский"
    other = "Другое"

class Role(str, Enum):
    dev = "dev"
    owner = "owner"
    admin = "admin"
    moderator = "moderator"
    user = "user"

class Hobby(str, Enum):
    anime = "Аниме"
    videogames = "Видеоигры"
    movies = "Фильмы"
    books = "Книги"
    doramas = "Дорамы"
    kpop = "К-Поп"
    music = "Музыка"
    other = "Другое"

class Orientation(str, Enum):
    hetero = "Гетеросексуал"
    bi = "Биcексуал"
    pan = "Пансексуал"
    gay = "Гей"
    lesbian = "Лесби"

class FType(str, Enum):
    basic = "Общение"
    romantic = "Отношения"


# --- GEO + ФИЛЬТРЫ --- #
class Geo(BaseModel):
    country: str
    country_code: str = None
    city: str

class Filters(BaseModel):
    geo: Geo
    age_from: int
    age_to: int
    sex: List[Gender]
    ftype: List[FType]
    hobby: List[Hobby]


# --- USER --- #
class User(BaseModel):
    tg_id: int
    role: Role = "user"
    name: str
    geo: Geo
    filters: Filters
    age: int
    sex: Gender
    hobby: List[Hobby]
    bio: str
    orientation: Orientation
    media: List[str]
    registered_at: int

    @staticmethod
    def _from_row(user: dict) -> 'User':
        return User(
            tg_id=user["tg_id"],
            role=user["role"],
            name=user["name"],
            geo=Geo(**json.loads(user["geo"])),
            filters=Filters(**json.loads(user["filters"])),
            age=user["age"],
            sex=user["sex"],
            hobby=json.loads(user["hobby"]),
            bio=user["bio"],
            orientation=user["orientation"],
            media=json.loads(user["media"]),
            registered_at=user["registered_at"]
        )

    @classmethod
    def create(cls, **kwargs) -> int:
        db = DB.get()
        sql = """
            INSERT INTO users (
                tg_id, role, name, geo, filters, age, sex, hobby, bio, orientation, media, registered_at
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        args = (
            kwargs["tg_id"],
            str(kwargs["role"].value) if isinstance(kwargs["role"], Enum) else kwargs["role"],
            kwargs["name"],
            json.dumps(kwargs["geo"]),
            json.dumps(kwargs["filters"]),
            kwargs["age"],
            str(kwargs["sex"].value) if isinstance(kwargs["sex"], Enum) else kwargs["sex"],
            json.dumps(kwargs["hobby"]),
            kwargs["bio"],
            str(kwargs["orientation"].value) if isinstance(kwargs["orientation"], Enum) else kwargs["orientation"],
            json.dumps(kwargs["media"]),
            kwargs["registered_at"]
        )
        db.execute(sql, args)
        db.clear_cache()
        user_id = db.query("SELECT LAST_INSERT_ID() AS id")[0]['id']
        return user_id

    @classmethod
    def get(cls, tg_id: int) -> Optional[Self]:
        db = DB.get()
        result = db.query("SELECT * FROM users WHERE tg_id = %s", (tg_id,), use_cache=True, cache_key=f"user:{tg_id}")
        if not result:
            return None
        return cls._from_row(result[0])

    def update(self, **kwargs) -> None:
        db = DB.get()
        fields = []
        values = []
        for k, v in kwargs.items():
            if k in ['geo', 'filters', 'hobby', 'media']:
                v = json.dumps(v)
            fields.append(f"{k} = %s")
            values.append(v)
        sql = f"UPDATE users SET {', '.join(fields)} WHERE tg_id = %s"
        values.append(self.tg_id)
        db.execute(sql, tuple(values))
        db.clear_cache()

    def delete(self) -> None:
        db = DB.get()
        db.execute("DELETE FROM users WHERE tg_id = %s", (self.tg_id,))
        db.clear_cache()

    @classmethod
    def get_all(cls, cache_seconds: int = 2) -> List[Self]:
        db = DB.get()
        cache_key = "_user_all"
        now = time.time()
        if "_ts" not in db.cache.cache or now - db.cache.access_time.get(cache_key, 0) > cache_seconds:
            users = db.query("SELECT * FROM users", use_cache=True, cache_key=cache_key)
            db.cache.set(cache_key, users)
        else:
            users = db.cache.get(cache_key)
        return [cls._from_row(user) for user in users]


# --- ANKETA --- #
class Anketa:
    def __init__(self, owner_user: User):
        self.owner_user = owner_user

    @staticmethod
    def search(filters: Filters, exclude_ids: Optional[List[int]] = None, limit: int = 1) -> List['Anketa']:
        exclude_ids = exclude_ids or []
        all_users = User.get_all()

        def log(msg):
            if DEBUG:
                print(msg)

        log(f"🔍 Поиск: пол={filters.sex}, возраст={filters.age_from}-{filters.age_to}, город={filters.geo.city}, страна={filters.geo.country}")
        log(f"❌ Исключаем ID: {exclude_ids}")

        def match(user: User, strict: bool = True) -> bool:
            if user.tg_id in exclude_ids:
                return False
            if filters.sex and user.sex not in filters.sex:
                return False
            if filters.age_from and user.age < filters.age_from:
                return False
            if filters.age_to and user.age > filters.age_to:
                return False
            if strict:
                if filters.geo.city and user.geo.city != filters.geo.city:
                    return False
            else:
                if filters.geo.country and user.geo.country != filters.geo.country:
                    return False
            return True

        matches = [user for user in all_users if match(user, strict=True)]

        if not matches and filters.geo.country:
            matches = [user for user in all_users if match(user, strict=False)]

        if not matches:
            matches = [user for user in all_users if user.tg_id not in exclude_ids]

        random.shuffle(matches)
        return [Anketa(owner_user=u) for u in matches[:limit]]

    def add_like(self, from_id: int) -> bool:
        db = DB.get()
        to_id = self.owner_user.tg_id
        created_at = int(time.time())

        try:
            mutual = db.query("SELECT 1 FROM likes WHERE from_id = %s AND to_id = %s", (to_id, from_id))
            is_mutual = bool(mutual)

            db.execute("""
                INSERT INTO likes (from_id, to_id, created_at, matched)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE matched = VALUES(matched)
            """, (from_id, to_id, created_at, is_mutual))

            if is_mutual:
                db.execute("UPDATE likes SET matched = TRUE WHERE from_id = %s AND to_id = %s", (to_id, from_id))

            return is_mutual

        except Exception as e:
            if DEBUG:
                print(f"⚠️ Ошибка при лайке: {e}")
            return False

    @staticmethod
    def is_mutual_like(user1_id: int, user2_id: int) -> bool:
        db = DB.get()
        result = db.query("""
            SELECT matched FROM likes WHERE 
            (from_id = %s AND to_id = %s) OR (from_id = %s AND to_id = %s)
        """, (user1_id, user2_id, user2_id, user1_id))
        return any(row["matched"] for row in result)

    def total_likes(self) -> int:
        db = DB.get()
        res = db.query("SELECT COUNT(*) AS cnt FROM likes WHERE to_id = %s", (self.owner_user.tg_id,))
        return res[0]['cnt'] if res else 0

    def total_mutual_likes(self) -> int:
        db = DB.get()
        res = db.query("SELECT COUNT(*) AS cnt FROM likes WHERE to_id = %s AND matched = TRUE", (self.owner_user.tg_id,))
        return res[0]['cnt'] if res else 0

    def get_liked_you(self) -> List[User]:
        db = DB.get()
        rows = db.query("SELECT from_id FROM likes WHERE to_id = %s", (self.owner_user.tg_id,))
        ids = set(row["from_id"] for row in rows)
        return [u for u in User.get_all() if u.tg_id in ids]

    def get_you_liked(self) -> List[User]:
        db = DB.get()
        rows = db.query("SELECT to_id FROM likes WHERE from_id = %s", (self.owner_user.tg_id,))
        ids = set(row["to_id"] for row in rows)
        return [u for u in User.get_all() if u.tg_id in ids]
    
    def get_mutual_likes(self) -> List[User]:
        db = DB.get()
        rows = db.query("SELECT from_id FROM likes WHERE to_id = %s AND matched = TRUE", (self.owner_user.tg_id,))
        ids = set(row["from_id"] for row in rows)
        return [u for u in User.get_all() if u.tg_id in ids]
