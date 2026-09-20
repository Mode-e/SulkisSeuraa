import db

def get_all_shifts():
    sql = """
        SELECT shifts.id, shifts.user_id, users.username, shifts.location, 
               shifts.time, shifts.player_level, shifts.player_count, shifts.total_players 
        FROM shifts 
        JOIN users ON shifts.user_id = users.id
    """
    return db.query(sql)

def get_upcoming_shifts(user_id, time_now):
    sql = """
        SELECT shifts.id, shifts.user_id, users.username, shifts.location, 
               shifts.time, shifts.player_level, shifts.player_count, shifts.total_players 
        FROM shifts 
        JOIN users ON shifts.user_id = users.id
        WHERE shifts.user_id = ? AND shifts.time >= ?
        ORDER BY shifts.time ASC
    """
    return list(db.query(sql, [user_id, time_now]))

def get_past_shifts(user_id, time_now):
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
        SELECT id, user_id, location, time, player_level, player_count, total_players 
        FROM shifts 
        WHERE id = ?
    """
    result = db.query(sql, [shift_id])
    return result[0]

def update_shift(shift_id, location, time, player_level, total_players):
    sql = """
        UPDATE shifts 
        SET location = ?, time = ?, player_level = ?, total_players = ? 
        WHERE id = ?
    """
    db.execute(sql, [location, time, player_level, total_players, shift_id])