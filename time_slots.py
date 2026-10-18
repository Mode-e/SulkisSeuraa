import db


def upcoming_slots(time_now, user_id=None):
    sql = """
        SELECT T.id, T.user_id, U.username, L.name AS location, 
            T.slot_time AS time, P.level_name AS player_level, 
            M.amount AS total_players, COUNT(S_count.id) AS player_count
        FROM time_slots T
        JOIN users U ON T.user_id = U.id
        LEFT JOIN locations L ON T.location_id = L.id
        LEFT JOIN player_levels P ON T.level_id = P.id
        LEFT JOIN total_players M ON T.max_players_id = M.id
        LEFT JOIN signups S_count ON T.id = S_count.slot_id
    """
    params = []

    if user_id is not None:
        sql += """
            JOIN signups S_filter ON T.id = S_filter.slot_id 
            WHERE S_filter.user_id = ? AND T.slot_time >= ? 
        """
        params = [user_id, time_now]
    else:
        sql += " WHERE T.slot_time >= ? "
        params = [time_now]

    sql += """
        GROUP BY T.id
        ORDER BY T.slot_time ASC
    """

    return list(db.query(sql, params))


def past_slots(user_id, time_now):
    sql = """
        SELECT T.id, T.user_id, U.username, L.name AS location, 
            T.slot_time AS time, P.level_name AS player_level, 
            M.amount AS total_players, COUNT(S_count.id) AS player_count
        FROM time_slots T
        JOIN signups S_filter ON T.id = S_filter.slot_id
        JOIN users U ON T.user_id = U.id
        LEFT JOIN locations L ON T.location_id = L.id
        LEFT JOIN player_levels P ON T.level_id = P.id
        LEFT JOIN total_players M ON T.max_players_id = M.id
        LEFT JOIN signups S_count ON T.id = S_count.slot_id
        WHERE S_filter.user_id = ? AND T.slot_time < ?
        GROUP BY T.id
        ORDER BY T.slot_time DESC
    """
    return list(db.query(sql, [user_id, time_now]))


def get_slot(slot_id):
    sql = """
        SELECT T.id, T.user_id, U.username, L.name AS location, 
            T.slot_time, P.level_name AS player_level, 
            M.amount AS total_players, COUNT(S.id) AS player_count
        FROM time_slots T
        JOIN users U ON T.user_id = U.id
        LEFT JOIN locations L ON T.location_id = L.id
        LEFT JOIN player_levels P ON T.level_id = P.id
        LEFT JOIN total_players M ON T.max_players_id = M.id
        LEFT JOIN signups S ON T.id = S.slot_id
        WHERE T.id = ?
        GROUP BY T.id
    """
    res = db.query(sql, [slot_id])

    if not res:
        return None
    return res[0]


def last_slot(user_id):
    sql = "SELECT id FROM time_slots WHERE user_id = ? ORDER BY id DESC LIMIT 1"
    result = db.query(sql, [user_id])
    if not result:
        return None
    return result[0]["id"]


def update_slot(slot_id, location_id, slot_time, level_id, max_players_id):
    sql = """
        UPDATE time_slots
        SET location_id = ?, 
            slot_time = ?, 
            level_id = ?, 
            max_players_id = ?
        WHERE id = ?
    """
    db.execute(sql, [location_id, slot_time, level_id, max_players_id, slot_id])


def get_players(slot_id):
    sql = """
        SELECT U.id, U.username 
        FROM signups S
        JOIN users U ON S.user_id = U.id
        WHERE S.slot_id = ?
    """
    return db.query(sql, [slot_id])


def my_slots(user_id, time_now):
    sql = """
        SELECT T.id, T.user_id, U.username, L.name AS location, 
            T.slot_time AS time, P.level_name AS player_level, 
            M.amount AS total_players, COUNT(S_count.id) AS player_count
        FROM time_slots T
        JOIN signups SU ON T.id = SU.slot_id
        JOIN users U ON T.user_id = U.id
        LEFT JOIN locations L ON T.location_id = L.id
        LEFT JOIN player_levels P ON T.level_id = P.id
        LEFT JOIN total_players M ON T.max_players_id = M.id
        LEFT JOIN signups S_count ON T.id = S_count.slot_id
        WHERE SU.user_id = ? AND T.slot_time > ?
        GROUP BY T.id
        ORDER BY T.slot_time ASC
    """
    return list(db.query(sql, [user_id, time_now]))


def available_slots(user_id, time_now):
    sql = """
        SELECT 
            T.id, T.user_id, U.username, L.name AS location, 
            T.slot_time AS time, P.level_name AS player_level, 
            M.amount AS total_players, COUNT(S.id) AS player_count
        FROM time_slots T
        JOIN users U ON T.user_id = U.id
        LEFT JOIN locations L ON T.location_id = L.id
        LEFT JOIN player_levels P ON T.level_id = P.id
        LEFT JOIN total_players M ON T.max_players_id = M.id
        LEFT JOIN signups S ON T.id = S.slot_id
        WHERE T.slot_time >= ? AND T.id NOT IN (
            SELECT slot_id FROM signups WHERE user_id = ?
        )
        GROUP BY T.id
        ORDER BY T.slot_time ASC
    """
    return db.query(sql, [time_now, user_id])


def cancel_signup(user_id, slot_id):
    sql = """
        DELETE FROM signups 
        WHERE user_id = ? AND slot_id = ?
    """
    db.execute(sql, [user_id, slot_id])


def signup(user_id, slot_id):
    sql = """
        INSERT INTO signups (user_id, slot_id) 
        VALUES (?, ?)
    """
    db.execute(sql, [user_id, slot_id])


def create_slot(slot_data):
    sql = """
        INSERT INTO time_slots (user_id, location_id, slot_time, level_id, max_players_id)
        VALUES (?, ?, ?, ?, ?)
    """
    db.execute(
        sql,
        [
            slot_data["user_id"],
            slot_data["location_id"],
            slot_data["slot_time"],
            slot_data["level_id"],
            slot_data["max_players_id"],
        ],
    )
    result = db.query("SELECT MAX(id) AS id FROM time_slots", [])
    if result:
        return result[0]["id"]
    return None


def delete_slot(slot_id):
    sql = "DELETE FROM signups WHERE slot_id = ?"
    db.execute(sql, [slot_id])

    sql = "DELETE FROM time_slots WHERE id = ?"
    db.execute(sql, [slot_id])


def created_slots(user_id, time_now):
    sql = """
        SELECT T.id, T.user_id, U.username, L.name AS location, 
            T.slot_time AS time, P.level_name AS player_level, 
            M.amount AS total_players, COUNT(S.id) AS player_count
        FROM time_slots T
        JOIN users U ON T.user_id = U.id
        LEFT JOIN locations L ON T.location_id = L.id
        LEFT JOIN player_levels P ON T.level_id = P.id
        LEFT JOIN total_players M ON T.max_players_id = M.id
        LEFT JOIN signups S ON T.id = S.slot_id
        WHERE T.user_id = ? AND T.slot_time >= ?
        GROUP BY T.id
        ORDER BY T.slot_time ASC
    """
    return db.query(sql, [user_id, time_now])


def all_created_slots(user_id):
    sql = """
        SELECT COUNT(id) 
        FROM time_slots 
        WHERE user_id = ?
    """
    res = db.query(sql, [user_id])
    if res:
        return res[0][0]
    return 0


def get_locations():
    return db.query("SELECT id, name FROM locations", [])


def get_levels():
    return db.query("SELECT id, level_name FROM player_levels", [])


def get_total():
    return db.query("SELECT id, amount FROM total_players", [])


def get_location_id(location_name):
    sql = db.query("SELECT id FROM locations WHERE name = ?", [location_name])
    if sql and len(sql) > 0:
        return sql[0]["id"]
    return None


def get_level_id(level_name):
    sql = db.query("SELECT id FROM player_levels WHERE level_name = ?", [level_name])
    if sql and len(sql) > 0:
        return sql[0]["id"]
    return None


def get_max_id(amount):
    sql = db.query("SELECT id FROM total_players WHERE amount = ?", [amount])
    if sql:
        return sql[0]["id"]
    return None


def get_messages(slot_id):
    sql = """
        SELECT id, slot_id, sender_username, text, timestamp
        FROM messages
        WHERE slot_id = ?
        ORDER BY timestamp ASC
    """
    return db.query(sql, [slot_id])


def add_message(slot_id, sender_username, text):
    sql = """
        INSERT INTO messages (slot_id, sender_username, text)
        VALUES (?, ?, ?)
    """
    db.execute(sql, [slot_id, sender_username, text])


def get_edit_message(message_id):
    sql = """
        SELECT id, slot_id, sender_username, text, timestamp
        FROM messages
        WHERE id = ?
    """
    result = db.query(sql, [message_id])
    if not result:
        return None
    return result[0]


def delete_message(message_id):
    sql = "DELETE FROM messages WHERE id = ?"
    db.execute(sql, [message_id])


def update_message(message_id, new_text):
    sql = "UPDATE messages SET text = ? WHERE id = ?"
    db.execute(sql, [new_text, message_id])


def get_upcoming_slots_paged(time_now, page, page_size, user_id=None):
    sql = """
        SELECT T.id, T.user_id, U.username, L.name AS location,
               T.slot_time AS time, P.level_name AS player_level,
               M.amount AS total_players,
               (SELECT COUNT(id) FROM signups WHERE slot_id = T.id) AS player_count
        FROM time_slots T
        JOIN users U ON T.user_id = U.id
        LEFT JOIN locations L ON T.location_id = L.id
        LEFT JOIN player_levels P ON T.id = P.id
        LEFT JOIN total_players M ON T.max_players_id = M.id
        WHERE T.slot_time >= ?
    """
    params = [time_now]

    if user_id is not None:
        sql += " AND T.id NOT IN (SELECT slot_id FROM signups WHERE user_id = ?) "
        params.append(user_id)
    limit = page_size
    offset = page_size * (page - 1)

    sql += """
        ORDER BY T.slot_time ASC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    return list(db.query(sql, params))


def get_upcoming_slots_count(time_now, user_id=None):
    sql = "SELECT COUNT(id) AS total FROM time_slots WHERE slot_time >= ?"
    params = [time_now]

    if user_id is not None:
        sql += " AND id NOT IN (SELECT slot_id FROM signups WHERE user_id = ?)"
        params.append(user_id)

    result = db.query(sql, params)
    if result:
        if isinstance(result, list):
            return result[0]["total"]
        return result["total"]
    return 0


def get_created_slots_count(time_now, user_id):
    sql = (
        "SELECT COUNT(id) AS total FROM time_slots WHERE slot_time >= ? AND user_id = ?"
    )
    result = db.query(sql, [time_now, user_id])
    if result:
        if isinstance(result, list):
            return result[0]["total"]
        return result["total"]
    return 0


def get_created_slots_paged(time_now, user_id, page, page_size):
    sql = """
        SELECT T.id, T.user_id, U.username, L.name AS location,
               T.slot_time AS time, P.level_name AS player_level,
               M.amount AS total_players,
               (SELECT COUNT(id) FROM signups WHERE slot_id = T.id) AS player_count
        FROM time_slots T
        JOIN users U ON T.user_id = U.id
        LEFT JOIN locations L ON T.location_id = L.id
        LEFT JOIN player_levels P ON T.id = P.id
        LEFT JOIN total_players M ON T.max_players_id = M.id
        WHERE T.slot_time >= ? AND T.user_id = ?
        ORDER BY T.slot_time ASC
        LIMIT ? OFFSET ?
    """
    limit = page_size
    offset = page_size * (page - 1)

    return list(db.query(sql, [time_now, user_id, limit, offset]))


def get_my_upcoming_count(time_now, user_id):
    sql = """
        SELECT COUNT(T.id) AS total 
        FROM time_slots T
        JOIN signups S ON T.id = S.slot_id
        WHERE T.slot_time >= ? AND S.user_id = ?
    """
    result = db.query(sql, [time_now, user_id])
    if result:
        return result[0]["total"] if isinstance(result, list) else result["total"]
    return 0


def get_my_upcoming_paged(time_now, user_id, page, page_size):
    sql = """
        SELECT T.id, T.user_id, U.username, L.name AS location,
               T.slot_time AS time, P.level_name AS player_level,
               M.amount AS total_players,
               (SELECT COUNT(id) FROM signups WHERE slot_id = T.id) AS player_count
        FROM time_slots T
        JOIN users U ON T.user_id = U.id
        JOIN signups S ON T.id = S.slot_id
        LEFT JOIN locations L ON T.location_id = L.id
        LEFT JOIN player_levels P ON T.id = P.id
        LEFT JOIN total_players M ON T.max_players_id = M.id
        WHERE T.slot_time >= ? AND S.user_id = ?
        ORDER BY T.slot_time ASC
        LIMIT ? OFFSET ?
    """
    limit = page_size
    offset = page_size * (page - 1)
    return list(db.query(sql, [time_now, user_id, limit, offset]))


def get_my_past_count(time_now, user_id):
    sql = """
        SELECT COUNT(id) AS total 
        FROM time_slots T
        JOIN signups S ON T.id = S.slot_id
        WHERE T.slot_time < ? AND S.user_id = ?
    """
    result = db.query(sql, [time_now, user_id])
    if result:
        return result[0]["total"] if isinstance(result, list) else result["total"]
    return 0


def get_my_past_paged(time_now, user_id, page, page_size):
    sql = """
        SELECT T.id, T.user_id, U.username, L.name AS location,
               T.slot_time AS time, P.level_name AS player_level,
               M.amount AS total_players,
               (SELECT COUNT(id) FROM signups WHERE slot_id = T.id) AS player_count
        FROM time_slots T
        JOIN users U ON T.user_id = U.id
        JOIN signups S ON T.id = S.slot_id
        LEFT JOIN locations L ON T.location_id = L.id
        LEFT JOIN player_levels P ON T.id = P.id
        LEFT JOIN total_players M ON T.max_players_id = M.id
        WHERE T.slot_time < ? AND S.user_id = ?
        ORDER BY T.slot_time DESC  -- Menneet vuorot näytetään uusimmasta vanhimpaan
        LIMIT ? OFFSET ?
    """
    limit = page_size
    offset = page_size * (page - 1)
    return list(db.query(sql, [time_now, user_id, limit, offset]))


def count_found_slots(time_now, location, day, player_level, total_players, username):
    sql = """
        SELECT COUNT(T.id) AS total
        FROM time_slots T
        JOIN users U ON T.user_id = U.id
        LEFT JOIN locations L ON T.location_id = L.id
        LEFT JOIN player_levels P ON T.level_id = P.id  -- KORJATTU: T.id -> T.level_id
        LEFT JOIN total_players M ON T.max_players_id = M.id
        WHERE T.slot_time >= ?
    """
    params = [time_now]

    if location:
        sql += " AND L.name = ?"
        params.append(location)
    if day:
        sql += " AND DATE(T.slot_time) = ?"
        params.append(day)
    if player_level:
        sql += " AND P.level_name = ?"
        params.append(player_level)
    if total_players:
        sql += " AND M.amount = ?"
        params.append(total_players)
    if username:
        sql += " AND U.username LIKE ?"
        params.append(f"%{username}%")

    result = db.query(sql, params)
    if result:
        if isinstance(result, list):
            return result[0]["total"]
        return result["total"]
    return 0


def find_slots_paged(
    time_now, location, day, player_level, total_players, username, page, page_size
):
    sql = """
        SELECT T.id, T.user_id, U.username, L.name AS location,
               T.slot_time AS time, P.level_name AS player_level,
               M.amount AS total_players,
               (SELECT COUNT(id) FROM signups WHERE slot_id = T.id) AS player_count
        FROM time_slots T
        JOIN users U ON T.user_id = U.id
        LEFT JOIN locations L ON T.location_id = L.id
        LEFT JOIN player_levels P ON T.level_id = P.id
        LEFT JOIN total_players M ON T.max_players_id = M.id
        WHERE T.slot_time >= ?
    """
    params = [time_now]

    if location:
        sql += " AND L.name = ?"
        params.append(location)
    if day:
        sql += " AND DATE(T.slot_time) = ?"
        params.append(day)
    if player_level:
        sql += " AND P.level_name = ?"
        params.append(player_level)
    if total_players:
        sql += " AND M.amount = ?"
        params.append(total_players)
    if username:
        sql += " AND U.username LIKE ?"
        params.append(f"%{username}%")

    sql += " ORDER BY T.slot_time ASC LIMIT ? OFFSET ?"

    limit = page_size
    offset = page_size * (page - 1)
    params.extend([limit, offset])

    return list(db.query(sql, params))


def get_message_count(slot_id):
    sql = "SELECT COUNT(id) AS total FROM messages WHERE slot_id = ?"
    result = db.query(sql, [slot_id])
    if result:
        if isinstance(result, list):
            return result[0]["total"]
        return result["total"]
    return 0


def get_messages_paged(slot_id, page, page_size):
    sql = """
        SELECT id, slot_id, sender_username, text, timestamp
        FROM messages
        WHERE slot_id = ?
        ORDER BY id ASC
        LIMIT ? OFFSET ?
    """

    limit = page_size
    offset = page_size * (page - 1)

    return list(db.query(sql, [slot_id, limit, offset]))
