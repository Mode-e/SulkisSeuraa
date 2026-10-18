DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS signups;
DROP TABLE IF EXISTS time_slots;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS locations;
DROP TABLE IF EXISTS player_levels;
DROP TABLE IF EXISTS total_players;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    player_level TEXT,
    description TEXT,
    profile_ready INTEGER DEFAULT 0,
    modified_slots_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS time_slots (
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

CREATE TABLE IF NOT EXISTS signups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    slot_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (slot_id) REFERENCES time_slots (id)
);

CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS player_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS total_players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount INTEGER UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id INTEGER NOT NULL,
    sender_username TEXT NOT NULL,
    text TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (slot_id) REFERENCES time_slots (id)
);

CREATE INDEX IF NOT EXISTS idx_time_slots_time ON time_slots(slot_time);
CREATE INDEX IF NOT EXISTS idx_time_slots_location ON time_slots(location_id);
CREATE INDEX IF NOT EXISTS idx_time_slots_level ON time_slots(level_id);
CREATE INDEX IF NOT EXISTS idx_messages_slot ON messages(slot_id);
CREATE INDEX IF NOT EXISTS idx_signups_slot ON signups(slot_id);
