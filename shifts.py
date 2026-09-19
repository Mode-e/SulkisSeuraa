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