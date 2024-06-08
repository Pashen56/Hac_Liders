create table if not exists mainmenu (
id integer primary key autoincrement,
title text not null,
url text not null
);

CREATE TABLE IF NOT EXISTS posts (
id integer PRIMARY KEY AUTOINCREMENT,
title text NOT NULL,
text text NOT NULL,
url text NOT NULL,
time integer NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
id integer PRIMARY KEY AUTOINCREMENT,
name text NOT NULL,
email text NOT NULL,
psw text NOT NULL,
avatar BLOB DEFAULT NULL,
time integer NOT NULL
);

CREATE TABLE IF NOT EXISTS request_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    result text NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    latitude text NOT NULL,
    longitude text NOT NULL,
    Risk text NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
