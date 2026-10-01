import db

def upcoming_slots(time_now, user_id=None):
    sql = """
        SELECT T.id, T.user_id, U.username, T.location,
               T.time, T.player_level, T.player_count, T.total_players
        FROM time_slots T
        JOIN users U ON T.user_id = U.id
    """
    params = []

    if user_id is not None:
        sql += " JOIN signups ON T.id = signups.slot_id WHERE signups.user_id = ? AND T.time >= ?"
        params = [user_id, time_now]
    else:
        sql += " WHERE T.time >= ?"
        params = [time_now]

    sql += " ORDER BY T.time ASC"
    
    return list(db.query(sql, params))

def past_slots(user_id, time_now):
    sql = """
        SELECT T.id, T.user_id, U.username, T.location,
               T.time, T.player_level, T.player_count, T.total_players
        FROM time_slots T
        JOIN signups ON T.id = signups.slot_id
        JOIN users U ON T.user_id = U.id
        WHERE signups.user_id = ? AND T.time < ?
        ORDER BY T.time DESC
    """
    return list(db.query(sql, [user_id, time_now]))

def get_slot(slot_id):
    sql = """
        SELECT T.id, T.user_id, T.location, T.time, T.player_level, T.player_count, T.total_players, U.username
        FROM time_slots T
        JOIN users U ON T.user_id = U.id
        WHERE T.id = ?
    """
    result = db.query(sql, [slot_id])

    if not result:
        return None
    return result[0]

def last_slot(user_id):
    sql = "SELECT id FROM time_slots WHERE user_id = ? ORDER BY id DESC LIMIT 1"
    result = db.query(sql, [user_id])
    if not result:
        return None
    return result[0]["id"]

def update_slot(slot_id, location, time, player_level, total_players):
    sql = """
        UPDATE time_slots 
        SET location = ?, time = ?, player_level = ?, total_players = ? 
        WHERE id = ?
    """
    db.execute(sql, [location, time, player_level, total_players, slot_id])

def find_slots(time_now, location=None, day=None, player_level=None, total_players=None, username=None):
    sql = """
        SELECT T.id, T.user_id, U.username, T.location, T.time,
                T.player_level, T.player_count, T.total_players
        FROM time_slots T
        JOIN users U ON T.user_id = U.id
        WHERE T.time > ?
    """
    params = [time_now]

    if location:
        sql += " AND T.location = ?"
        params.append(location)
    if day:
        sql += " AND T.time LIKE ?"
        params.append(f"{day}%")
    if player_level:
        sql += " AND T.player_level = ?"
        params.append(player_level)
    if total_players:
        sql += " AND T.total_players = ?"
        params.append(total_players)
    if username:
        sql += " AND U.username LIKE ?"
        params.append(f"%{username}%")

    sql += " ORDER BY T.time ASC"

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
        SELECT T.id, T.user_id, T.location, T.time, T.player_level, T.player_count, T.total_players, U.username
        FROM time_slots T
        JOIN users U ON T.user_id = U.id
        JOIN signups SU ON T.id = SU.slot_id
        WHERE SU.user_id = ? AND T.time > ?
        ORDER BY T.time ASC
    """
    return list(db.query(sql, [user_id, time_now]))

def available_slots(user_id, time_now):
    sql = """
        SELECT T.id, T.user_id, T.location, T.time, T.player_level,
                T.player_count, T.total_players, U.username
        FROM time_slots T
        JOIN users U ON T.user_id = U.id
        WHERE T.time >= ? AND T.id NOT IN (
            SELECT slot_id FROM signups WHERE user_id = ?
        )
        ORDER BY T.time ASC
    """
    return db.query(sql, [time_now, user_id])

def cancel_signup(user_id, slot_id):
    sql = """
        DELETE FROM signups 
        WHERE user_id = ? AND slot_id = ?
    """
    db.execute(sql, [user_id, slot_id])

def decrease_players(slot_id):
    sql = """
        UPDATE time_slots 
        SET player_count = player_count - 1 
        WHERE id = ?
    """
    db.execute(sql, [slot_id])

def signup(user_id, slot_id):
    sql = """
        INSERT INTO signups (user_id, slot_id) 
        VALUES (?, ?)
    """
    db.execute(sql, [user_id, slot_id])

def increase_player(slot_id):
    sql = """
        UPDATE time_slots 
        SET player_count = player_count + 1 
        WHERE id = ?
    """
    db.execute(sql, [slot_id])

def create_slot(slot_data):
    sql = """
        INSERT INTO time_slots (user_id, location, time, player_level, player_count, total_players)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    db.execute(sql, [slot_data["user_id"], slot_data["location"], 
        slot_data["time"], slot_data["player_level"], 
        slot_data["player_count"], slot_data["total_players"]])

def delete_slot(slot_id):
    sql = "DELETE FROM signups WHERE slot_id = ?"
    db.execute(sql, [slot_id])

    sql = "DELETE FROM time_slots WHERE id = ?"
    db.execute(sql, [slot_id])

def created_slots(user_id, time_now):
    sql = """
        SELECT T.id, T.user_id, U.username, T.location, T.time,
               T.player_level, T.player_count, T.total_players
        FROM time_slots T
        JOIN users U ON T.user_id = U.id
        WHERE T.user_id = ? AND T.time >= ?
        ORDER BY T.time ASC
    """
    return db.query(sql, [user_id, time_now])