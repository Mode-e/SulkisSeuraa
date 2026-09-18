import db

def get_all_shifts():
    sql = """
        SELECT shifts.id, shifts.user_id, users.username, shifts.location, 
               shifts.time, shifts.player_level, shifts.player_count, shifts.total_players 
        FROM shifts 
        JOIN users ON shifts.user_id = users.id
    """
    return db.query(sql)
