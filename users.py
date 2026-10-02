from werkzeug.security import check_password_hash
import db

def user_create(username, password_hash):
    sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
    db.execute(sql, [username, password_hash])

def user_login(username, password):
    sql = "SELECT id, password_hash FROM users WHERE username = ?"
    result = db.query(sql, [username])
    if not result:
        return None

    user_id = result[0]["id"]
    password_hash = result[0]["password_hash"]

    if check_password_hash(password_hash, password):
        return user_id
    return None

def user_info(user_id):
    sql = """
        SELECT username , player_level, description
        FROM users
        WHERE id = ?
    """
    return db.query(sql, [user_id])

def user_exists(username):
    sql = "SELECT 1 FROM users WHERE username = ?"
    result = db.query(sql, [username])
    return bool(result)

def user_update(user_data, user_id):
    sql = """
        UPDATE users 
        SET player_level = ?, description = ?
        WHERE id = ?
    """
    db.execute(sql, [user_data["player_level"], user_data["description"], user_id])
