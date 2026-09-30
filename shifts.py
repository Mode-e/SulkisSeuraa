import db

def upcoming_shifts(time_now, user_id=None):
    sql = """
        SELECT S.id, S.user_id, U.username, S.location,
               S.time, S.player_level, S.player_count, S.total_players
        FROM shifts S
        JOIN users U ON S.user_id = U.id
    """
    params = []

    if user_id is not None:
        sql += " JOIN signups ON S.id = signups.shift_id WHERE signups.user_id = ? AND S.time >= ?"
        params = [user_id, time_now]
    else:
        sql += " WHERE S.time >= ?"
        params = [time_now]

    sql += " ORDER BY S.time ASC"
    
    return list(db.query(sql, params))

def past_shifts(user_id, time_now):
    sql = """
        SELECT S.id, S.user_id, U.username, S.location,
               S.time, S.player_level, S.player_count, S.total_players
        FROM shifts S
        JOIN signups ON S.id = signups.shift_id
        JOIN users U ON S.user_id = U.id
        WHERE signups.user_id = ? AND S.time < ?
        ORDER BY S.time DESC
    """
    return list(db.query(sql, [user_id, time_now]))

def get_shift(shift_id):
    sql = """
        SELECT S.id, S.user_id, S.location, S.time, S.player_level, S.player_count, S.total_players, U.username
        FROM shifts S
        JOIN users U ON S.user_id = U.id
        WHERE S.id = ?
    """
    result = db.query(sql, [shift_id])

    if not result:
        return None
    return result[0]

def last_shift(user_id):
    sql = "SELECT id FROM shifts WHERE user_id = ? ORDER BY id DESC LIMIT 1"
    result = db.query(sql, [user_id])
    if not result:
        return None
    return result[0]["id"]

def update_shift(shift_id, location, time, player_level, total_players):
    sql = """
        UPDATE shifts 
        SET location = ?, time = ?, player_level = ?, total_players = ? 
        WHERE id = ?
    """
    db.execute(sql, [location, time, player_level, total_players, shift_id])

def find_shifts(time_now, location=None, day=None, player_level=None, total_players=None, username=None):
    sql = """
        SELECT S.id, S.user_id, U.username, S.location, S.time,
                S.player_level, S.player_count, S.total_players
        FROM shifts S
        JOIN users U ON S.user_id = U.id
        WHERE S.time > ?
    """
    params = [time_now]

    if location:
        sql += " AND S.location = ?"
        params.append(location)
    if day:
        sql += " AND S.time LIKE ?"
        params.append(f"{day}%")
    if player_level:
        sql += " AND S.player_level = ?"
        params.append(player_level)
    if total_players:
        sql += " AND S.total_players = ?"
        params.append(total_players)
    if username:
        sql += " AND U.username LIKE ?"
        params.append(f"%{username}%")

    sql += " ORDER BY S.time ASC"

    return db.query(sql, params)

def get_players(shift_id):
    sql = """
        SELECT U.username 
        FROM signups S
        JOIN users U ON S.user_id = U.id
        WHERE S.shift_id = ?
    """
    return db.query(sql, [shift_id])

def my_shifts(user_id, time_now):
    sql = """
        SELECT S.id, S.user_id, S.location, S.time, S.player_level, S.player_count, S.total_players, U.username
        FROM shifts S
        JOIN users U ON S.user_id = U.id
        JOIN signups SU ON S.id = SU.shift_id
        WHERE SU.user_id = ? AND S.time > ?
        ORDER BY S.time ASC
    """
    return db.query(sql, [user_id, time_now])

def available_shifts(user_id, time_now):
    sql = """
        SELECT S.id, S.user_id, S.location, S.time, S.player_level,
                S.player_count, S.total_players, U.username
        FROM shifts S
        JOIN users U ON S.user_id = U.id
        WHERE S.time >= ? AND S.id NOT IN (
            SELECT shift_id FROM signups WHERE user_id = ?
        )
        ORDER BY S.time ASC
    """
    return db.query(sql, [time_now, user_id])

def cancel_signup(user_id, shift_id):
    sql = """
        DELETE FROM signups 
        WHERE user_id = ? AND shift_id = ?
    """
    db.execute(sql, [user_id, shift_id])

def decrease_players(shift_id):
    sql = """
        UPDATE shifts 
        SET player_count = player_count - 1 
        WHERE id = ?
    """
    db.execute(sql, [shift_id])

def signup(user_id, shift_id):
    sql = """
        INSERT INTO signups (user_id, shift_id) 
        VALUES (?, ?)
    """
    db.execute(sql, [user_id, shift_id])

def increase_player(shift_id):
    sql = """
        UPDATE shifts 
        SET player_count = player_count + 1 
        WHERE id = ?
    """
    db.execute(sql, [shift_id])

def create_shift(shift_data):
    sql = """
        INSERT INTO shifts (user_id, location, time, player_level, player_count, total_players)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    db.execute(sql, [shift_data["user_id"], shift_data["location"], 
        shift_data["time"], shift_data["player_level"], 
        shift_data["player_count"], shift_data["total_players"]])

def delete_shift(shift_id):
    sql = "DELETE FROM signups WHERE shift_id = ?"
    db.execute(sql, [shift_id])

    sql = "DELETE FROM shifts WHERE id = ?"
    db.execute(sql, [shift_id])

def created_shifts(user_id, time_now):
    sql = """
        SELECT S.id, S.user_id, U.username, S.location, S.time,
               S.player_level, S.player_count, S.total_players
        FROM shifts S
        JOIN users U ON S.user_id = U.id
        WHERE S.user_id = ? AND S.time >= ?
        ORDER BY S.time ASC
    """
    return db.query(sql, [user_id, time_now])