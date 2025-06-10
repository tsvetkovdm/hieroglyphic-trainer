DROP TABLE IF EXISTS "user_selection";
DROP TABLE IF EXISTS "training_item";
DROP TABLE IF EXISTS "character";
DROP TABLE IF EXISTS "training_session";
DROP TABLE IF EXISTS "user";
DROP TABLE IF EXISTS "radical_group";
DROP TABLE IF EXISTS "training_mode";
DROP TABLE IF EXISTS "role";


-- Таблицы без внешних ключей

CREATE TABLE "role" (
	"id" INTEGER PRIMARY KEY,
	"name" VARCHAR(30) UNIQUE NOT NULL
);

CREATE TABLE "training_mode" (
	"id" INTEGER PRIMARY KEY,
	"name" VARCHAR(50),
	"access_level" INTEGER NOT NULL,
	"description" VARCHAR(255) 
);

CREATE TABLE "radical_group" (
	"id" INTEGER INTEGER PRIMARY KEY,
	"name" VARCHAR(30) UNIQUE NOT NULL,
	"description" VARCHAR(255) NOT NULL 
);

-- Таблицы, зависящие от других таблиц

CREATE TABLE "user" (
    "id" INTEGER PRIMARY KEY,
	"username" VARCHAR(50) UNIQUE NOT NULL,
	"password" VARCHAR(255) NOT NULL,
	"first_name" VARCHAR(100) NOT NULL,
	"last_name" VARCHAR(100) NOT NULL,
	"email" VARCHAR(100) NOT NULL,
	"role_id" INT NOT NULL REFERENCES "role" ("id"),
	"date_of_birth" DATE
);

CREATE TABLE "training_session" (
	"id" INTEGER,
	"user_id" INTEGER REFERENCES "user" ("id"),
	"mode_id" INTEGER REFERENCES "training_mode" ("id"),
	"date_started" DATE,
	"date_ended" DATE,
	"result" VARCHAR(20),
	PRIMARY KEY("id", "user_id", "mode_id")
);

CREATE TABLE "character" (
	"id" INTEGER PRIMARY KEY,
	"symbol" VARCHAR(10) NOT NULL,
	"pinyin" VARCHAR(50) NOT NULL,
	"meaning" VARCHAR(255) NOT NULL,
	"stroke_order_image_url" VARCHAR(512),
	"description" VARCHAR(255),
	"group_id" INTEGER REFERENCES "radical_group" ("id")
);

CREATE TABLE "training_item" (
	"id" INTEGER,
	"session_id" INTEGER REFERENCES "training_session" ("id"),
	"character_id" INTEGER REFERENCES "character" ("id"),
	PRIMARY KEY ("id", "session_id")
);

CREATE TABLE "user_selection" (
	"id" INTEGER,
	"user_id" INTEGER REFERENCES "user" ("id"),
	"character_id" INTEGER REFERENCES "character" ("id"),
	PRIMARY KEY ("id", "user_id")
);
