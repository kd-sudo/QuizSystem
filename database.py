import sqlite3
import random
from paths import get_db_path

def generate_unique_pin(cursor):
    while True:
        pin = str(random.randint(100000, 999999))
        cursor.execute("SELECT id FROM tests WHERE access_code = ?", (pin,))
        if not cursor.fetchone():
            return pin

def init_db():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    # Таблиця користувачів (з підтримкою груп/класів для студентів)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('teacher', 'student')),
            group_name TEXT DEFAULT 'ПЗ-11'
        )
    """)

    # Таблиця тестів (з PIN-кодом, тегом предмету та статусом ефіру)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER,
            title TEXT NOT NULL,
            subject TEXT DEFAULT 'Загальний',
            description TEXT,
            access_code TEXT UNIQUE NOT NULL,
            time_limit INTEGER DEFAULT 25,
            max_attempts INTEGER DEFAULT 1,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (teacher_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    # Таблиця питань
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER,
            content TEXT NOT NULL,
            question_type TEXT NOT NULL CHECK(question_type IN ('single', 'multiple')),
            FOREIGN KEY (test_id) REFERENCES tests (id) ON DELETE CASCADE
        )
    """)

    # Таблиця варіантів відповідей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER,
            content TEXT NOT NULL,
            is_correct INTEGER NOT NULL CHECK(is_correct IN (0, 1)),
            FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE
        )
    """)

    # Таблиця спроб та результатів (з аналітикою швидкості та контролем фокусу)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            test_id INTEGER,
            score INTEGER NOT NULL,
            max_score INTEGER NOT NULL,
            game_points INTEGER DEFAULT 0,
            avg_time REAL DEFAULT 0.0,
            focus_lost_count INTEGER DEFAULT 0,
            attempt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (test_id) REFERENCES tests (id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()