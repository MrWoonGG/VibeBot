import mysql.connector
from config import DB_CFG
import bot
import asyncio

def create_users_table():
    conn = mysql.connector.connect(
        host=DB_CFG['host'],
        user=DB_CFG['user'],
        password=DB_CFG['password'],
        database=DB_CFG['database']
    )
    cursor = conn.cursor()

    # проверка users
    cursor.execute("SHOW TABLES LIKE 'users'")
    result = cursor.fetchone()

    if result:
        print("✅ MYSQL: Table `users` passed")
    else:
        print("📁 MYSQL: Table `users` not found, creating...")
        cursor.execute("""
            CREATE TABLE users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tg_id BIGINT NOT NULL UNIQUE,
                role VARCHAR(20) NOT NULL,
                name VARCHAR(100) NOT NULL,
                geo JSON NOT NULL,
                filters JSON NOT NULL,
                age INT NOT NULL,
                sex VARCHAR(10) NOT NULL,
                hobby JSON NOT NULL,
                bio TEXT NOT NULL,
                orientation VARCHAR(20) NOT NULL,
                media TEXT,
                registered_at INT NOT NULL
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
        """)
        conn.commit()
        print("✅ MYSQL: Table `users` created 🛠️")

    # проверка likes
    cursor.execute("SHOW TABLES LIKE 'likes'")
    result = cursor.fetchone()

    if result:
        print("✅ MYSQL: Table `likes` passed")
    else:
        print("📁 MYSQL: Table `likes` not found, creating...")
        cursor.execute("""
            CREATE TABLE likes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                from_id BIGINT NOT NULL,
                to_id BIGINT NOT NULL,
                created_at INT NOT NULL,
                matched BOOLEAN DEFAULT FALSE,
                UNIQUE KEY unique_like (from_id, to_id)
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
        """)
        conn.commit()
        print("✅ MYSQL: Table `likes` created")

    cursor.close()
    conn.close()


print("🔧 Status: Pre-Checks")
create_users_table()
print("🔧 Status: Running bot.py")
asyncio.run(bot.main())
