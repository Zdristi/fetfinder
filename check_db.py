import sqlite3
conn = sqlite3.connect('fetdate_local.db')
cursor = conn.cursor()

# Получим список таблиц
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print('Таблицы в базе данных:', tables)

# Посмотрим, есть ли пользователи
cursor.execute("SELECT COUNT(*) FROM user;")
user_count = cursor.fetchone()[0]
print(f'Количество пользователей: {user_count}')

# Если есть пользователи, посмотрим информацию о первом
if user_count > 0:
    cursor.execute("SELECT id, username, email, created_at FROM user LIMIT 5;")
    users = cursor.fetchall()
    print('Примеры пользователей (id, username, email, created_at):')
    for user in users:
        print(f'  {user}')

conn.close()