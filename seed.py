import random
import sqlite3
from datetime import datetime, timedelta


def generate():
    db = sqlite3.connect("database.db")
    cursor = db.cursor()
    with open("schema.sql", "r", encoding="utf-8") as f:
        schema_script = f.read()
    cursor.executescript(schema_script)
    db.commit()
    with open("init.sql", "r", encoding="utf-8") as f:
        init_script = f.read()
    cursor.executescript(init_script)
    db.commit()
    user_count = 1000
    slot_count = 10000
    message_count = 1000000
    users_data = []
    testi_password_hash = (
        "scrypt:32768:16:1$randomsalt$abcdefghijklmnopqrstuvwxyz123456"
    )
    for i in range(1, user_count + 1):
        username = f"user{i}"
        users_data.append(
            (username, testi_password_hash, "Harrastaja", "Moi! Olen testipelaaja.", 1)
        )
    cursor.executemany(
        """
        INSERT INTO users (username, password_hash, player_level, description, profile_ready) 
        VALUES (?, ?, ?, ?, ?)
    """,
        users_data,
    )
    cursor.execute("SELECT id FROM users")
    created_id_tuples = cursor.fetchall()
    user_id_list = [row[0] for row in created_id_tuples]
    slots_data = []
    signups_data = []
    start = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(
        hours=1
    )

    for i in range(1, slot_count + 1):
        slot_time = (start + timedelta(minutes=i * 30)).strftime("%Y-%m-%d %H:%M")
        user_id = random.choice(user_id_list)
        location_id = random.randint(1, 6)
        level_id = random.randint(1, 4)
        max_players_id = random.randint(1, 2)
        slots_data.append((user_id, location_id, slot_time, level_id, max_players_id))
        signups_data.append((user_id, i))

    cursor.executemany(
        """
        INSERT INTO time_slots (user_id, location_id, slot_time, level_id, max_players_id) 
        VALUES (?, ?, ?, ?, ?)
    """,
        slots_data,
    )

    cursor.executemany(
        """
        INSERT INTO signups (user_id, slot_id) 
        VALUES (?, ?)
    """,
        signups_data,
    )
    cursor.execute("SELECT COUNT(*) FROM signups")

    messages_data = []
    for i in range(1, message_count + 1):
        slot_id = random.randint(1, slot_count)
        sender_username = f"user{random.randint(1, user_count)}"
        text = f"Testiviesti {i}."
        messages_data.append((slot_id, sender_username, text))

    cursor.executemany(
        """
        INSERT INTO messages (slot_id, sender_username, text, timestamp) 
        VALUES (?, ?, ?, datetime('now'))
    """,
        messages_data,
    )

    try:
        db.commit()
        print("Kaikki testitiedot alustettu ja tallennettu onnistuneesti!")

    except sqlite3.Error as e:
        db.rollback()
        print(f"Virhe tallennuksessa, muutokset peruttu: {e}")

    finally:
        db.close()
        print("Tietokantayhteys suljettu.")


if __name__ == "__main__":
    generate()
