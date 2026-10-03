import db

def upcoming_slots(time_now, user_id=None):
    sql = sql = """
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
            M.amount AS total_players,COUNT(S_count.id) AS player_count
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

def find_slots(time_now, location_id=None, day=None, level_id=None,
                max_players_id=None, username=None):
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
        WHERE T.slot_time > ?
    """
    params = [time_now]

    if location_id and location_id != "":
        sql += " AND L.name LIKE ? "
        params.append(location_id)

    if day and day != "":
        sql += " AND T.slot_time LIKE ? "
        params.append(f"{day}%")

    if level_id and level_id != "":
        sql += " AND P.level_name LIKE ? "
        params.append(level_id)

    if max_players_id and max_players_id != "":
        sql += " AND M.amount LIKE ? "
        params.append(max_players_id)

    if username and username != "":
        sql += " AND U.username LIKE ? "
        params.append(f"%{username}%")

    sql += """
        GROUP BY T.id
        ORDER BY T.slot_time ASC
    """

    return db.query(sql, params)

def get_players(slot_id):
    sql = """
        SELECT U.username 
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
    db.execute(sql, [slot_data["user_id"], slot_data["location_id"],
        slot_data["slot_time"], slot_data["level_id"], slot_data["max_players_id"]
    ])

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
        SELECT COUNT(*) 
        FROM time_slots 
        WHERE user_id = ?
    """
    res  = db.query(sql, [user_id])
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
    if sql:
        return sql[0]["id"]
    return None

def get_level_id(level_name):
    row = db.query("SELECT id FROM player_levels WHERE level_name = ?", [level_name])
    if row:
        return row[0]["id"]
    return None

def get_max_id(amount):
    row = db.query("SELECT id FROM total_players WHERE amount = ?", [amount])
    if row:
        return row[0]["id"]
    return None
