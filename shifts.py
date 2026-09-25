import db

def get_all_shifts():
    sql = """
        SELECT shifts.id, shifts.user_id, users.username, shifts.location, 
               shifts.time, shifts.player_level, shifts.player_count, shifts.total_players 
        FROM shifts 
        JOIN users ON shifts.user_id = users.id
    """
    return db.query(sql)

def get_upcoming_shifts_all(time_now):
    sql = """
        SELECT shifts.id, shifts.user_id, users.username, shifts.location, 
               shifts.time, shifts.player_level, shifts.player_count, shifts.total_players 
        FROM shifts 
        JOIN users ON shifts.user_id = users.id
        WHERE shifts.time >= ?
        ORDER BY shifts.time ASC
    """
    return list(db.query(sql, [time_now]))

def get_upcoming_shifts_by_user(user_id, time_now):
    sql = """
        SELECT shifts.id, shifts.user_id, users.username, shifts.location, 
               shifts.time, shifts.player_level, shifts.player_count, shifts.total_players 
        FROM shifts 
        JOIN users ON shifts.user_id = users.id
        WHERE shifts.user_id = ? AND shifts.time >= ?
        ORDER BY shifts.time ASC
    """
    return list(db.query(sql, [user_id, time_now]))

def get_past_shifts_by_user(user_id, time_now):
    sql = """
        SELECT shifts.id, shifts.user_id, users.username, shifts.location, 
               shifts.time, shifts.player_level, shifts.player_count, shifts.total_players 
        FROM shifts 
        JOIN users ON shifts.user_id = users.id
        WHERE shifts.user_id = ? AND shifts.time < ?
        ORDER BY shifts.time DESC
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

def get_last_shift_id(user_id):
    sql = "SELECT id FROM shifts WHERE user_id = ? ORDER BY id DESC LIMIT 1"
    result = db.query(sql, [user_id])
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

def get_signed_up_players(shift_id):
    sql = """
        SELECT users.username 
        FROM signups
        JOIN users ON signups.user_id = users.id
        WHERE signups.shift_id = ?
    """
    return db.query(sql, [shift_id])

def get_my_signed_shifts(user_id, current_time):
    sql = """
        SELECT S.id, S.user_id, S.location, S.time, S.player_level, S.player_count, S.total_players, U.username
        FROM shifts S
        JOIN users U ON S.user_id = U.id
        JOIN signups SU ON S.id = SU.shift_id
        WHERE SU.user_id = ? AND S.time > ?
        ORDER BY S.time ASC
    """
    return db.query(sql, [user_id, current_time])


def get_available_shifts(user_id, current_time):
    sql = """
        SELECT S.id, S.user_id, S.location, S.time, S.player_level, S.player_count, S.total_players, U.username
        FROM shifts S
        JOIN users U ON S.user_id = U.id
        WHERE S.time > ? AND S.id NOT IN (
            SELECT shift_id FROM signups WHERE user_id = ?
        )
        ORDER BY S.time ASC
    """
    return db.query(sql, [current_time, user_id])

def cancel_registration(user_id, shift_id):
    sql = """
        UPDATE shifts 
        SET player_count = player_count - 1 
        WHERE id = ? AND EXISTS (
            SELECT 1 FROM signups WHERE user_id = ? AND shift_id = ?
        )
    """
    db.execute(sql, [shift_id, user_id, shift_id])

    sql1 = """
        DELETE FROM signups 
        WHERE user_id = ? AND shift_id = ?
    """
    db.execute(sql1, [user_id, shift_id])

def signup_registration(user_id, shift_id):
    sql = """
        INSERT INTO signups (user_id, shift_id) 
        VALUES (?, ?)
    """
    db.execute(sql, [user_id, shift_id])

    sql1 = """
        UPDATE shifts 
        SET player_count = player_count + 1 
        WHERE id = ?
    """
    db.execute(sql1, [shift_id])

def create_shift(shift_data):
    sql = """
        INSERT INTO shifts (user_id, location, time, player_level, player_count, total_players)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    db.execute(sql, [shift_data["user_id"], shift_data["location"], 
        shift_data["time"], shift_data["player_level"], 
        shift_data["player_count"], shift_data["total_players"]])

    shift_id = get_last_shift_id(shift_data["user_id"])

    sql = """
        INSERT INTO signups (user_id, shift_id) 
        VALUES (?, ?)
    """
    db.execute(sql, [shift_data["user_id"], shift_id])

    return shift_id

def check_login(username, password):
    sql = "SELECT id, password_hash FROM users WHERE username = ?"
    result = db.query(sql, [username])
    if not result:
        return None

    user_id = result[0]["id"]
    password_hash = result[0]["password_hash"]

    if check_password_hash(password_hash, password):
        return user_id
    else:
        return None

def create_user(username, password_hash):
    sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
    db.execute(sql, [username, password_hash])

def user_exists(username):
    sql = "SELECT 1 FROM users WHERE username = ?"
    result = db.query(sql, [username])
    return bool(result)