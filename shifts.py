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

def find_shifts(time_now, location=None, day=None, player_level=None, total_players=None):
    sql = """
        SELECT id, user_id, location, time,
                player_level, player_count, total_players
        FROM shifts
        WHERE time > ?
    """
    params = [time_now]

    if location:
        sql += " AND shifts.location = ?"
        params.append(location)
    if day:
        sql += " AND shifts.time LIKE ?"
        params.append(f"{day}%")
    if player_level:
        sql += " AND shifts.player_level = ?"
        params.append(player_level)
    if total_players:
        sql += " AND shifts.total_players = ?"
        params.append(total_players)

    sql += " ORDER BY shifts.time ASC"

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