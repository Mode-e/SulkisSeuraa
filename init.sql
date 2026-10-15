PRAGMA foreign_keys = OFF;
DELETE FROM messages;
DELETE FROM signups;
DELETE FROM time_slots;
DELETE FROM users;
DELETE FROM locations;
DELETE FROM player_levels;
DELETE FROM total_players;
DELETE FROM sqlite_sequence;
PRAGMA foreign_keys = ON;

INSERT INTO locations (name) VALUES ("Kluuvi Unisport");
INSERT INTO locations (name) VALUES ("Kumpula Unisport");
INSERT INTO locations (name) VALUES ("Meilahti Unisport");
INSERT INTO locations (name) VALUES ("Otaniemi Unisport");
INSERT INTO locations (name) VALUES ("Töölö Unisport");
INSERT INTO locations (name) VALUES ("Viikki Unisport");

INSERT INTO player_levels (level_name) VALUES ('Aloittelija');
INSERT INTO player_levels (level_name) VALUES ('Harrastaja');
INSERT INTO player_levels (level_name) VALUES ('Aktiivipelaaja');
INSERT INTO player_levels (level_name) VALUES ('Kilpapelaaja');

INSERT INTO total_players (amount) VALUES ("2");
INSERT INTO total_players (amount) VALUES ("4");
