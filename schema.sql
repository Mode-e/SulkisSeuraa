CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    player_level TEXT,
    description TEXT,
    profile_ready INTEGER DEFAULT 0
);

CREATE TABLE shifts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    location TEXT NOT NULL,
    time TEXT NOT NULL,
    player_level TEXT NOT NULL,
    player_count INTEGER DEFAULT 0,
    total_players INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE signups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    shift_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (shift_id) REFERENCES shifts (id)
);
