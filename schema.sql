CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    player_level TEXT,
    description TEXT,
    profile_ready INTEGER DEFAULT 0
);

CREATE TABLE time_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    slot_time DATETIME NOT NULL,
    level_id INTEGER NOT NULL,       
    max_players_id INTEGER NOT NULL, 
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (location_id) REFERENCES locations (id),
    FOREIGN KEY (level_id) REFERENCES player_levels (id),
    FOREIGN KEY (max_players_id) REFERENCES total_players (id)
);

CREATE TABLE signups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    slot_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (slot_id) REFERENCES time_slots (id)
);

CREATE TABLE locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE player_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level_name TEXT UNIQUE NOT NULL
);

CREATE TABLE total_players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount INTEGER UNIQUE NOT NULL
);
