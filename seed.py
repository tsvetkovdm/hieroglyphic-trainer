import csv
import os

from app.db import get_connection
from werkzeug.security import generate_password_hash

CSV_DIR = os.path.join("db", "csv")

def copy_table(conn, table_name, csv_filename, columns):
    file_path = os.path.join(CSV_DIR, csv_filename)
    with conn.cursor() as cur, open(file_path, encoding="utf-8") as f:
        with cur.copy(
            f'''COPY {table_name} ({', '.join(columns)}) 
                FROM STDIN WITH (FORMAT CSV, HEADER TRUE, DELIMITER ';')'''
        ) as copy:
            for line in f:
                copy.write(line)
    print(f" Imported: {table_name}")

def seed_users(conn):
    file_path = os.path.join(CSV_DIR, "user.csv")
    with conn.cursor() as cur, open(file_path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            hashed_password = generate_password_hash(row['password'])
            cur.execute(
                '''INSERT INTO "user" 
                   (username, password, first_name, last_name, email, date_of_birth, role_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                (row['username'], hashed_password, row['first_name'], row['last_name'],
                 row['email'], row['date_of_birth'], row['role_id'])
            )
    print(" Imported users with hashed passwords")

def main():
    with get_connection() as conn:
        copy_table(conn, '"role"', 'role.csv', ['name'])
        copy_table(conn, '"training_mode"', 'training_mode.csv', ['name', 'access_level', 'description'])
        copy_table(conn, '"radical_group"', 'radical_group.csv', ['name', 'slug', 'description'])
        seed_users(conn)
        copy_table(conn, '"learning_object"', 'learning_object.csv',
                   ['symbol', 'pinyin', 'meaning', 'stroke_order_image_url', 'description', 'slug', 'group_id'])
        copy_table(conn, '"training_session"', 'training_session.csv',
                   ['user_id', 'mode_id', 'date_started', 'date_ended', 'result'])
        copy_table(conn, '"training_item"', 'training_item.csv', ['session_id', 'object_id'])
        copy_table(conn, '"user_selection"', 'user_selection.csv', ['user_id', 'object_id', 'saved_name'])

        conn.commit()
        print("Seeding completed.")

if __name__ == "__main__":
    main()
