import sqlite3
conn = sqlite3.connect('fetdate_local.db')
cursor = conn.cursor()

# Посмотрим, как выглядят хэши паролей
cursor.execute("SELECT id, username, password_hash FROM user LIMIT 5;")
users = cursor.fetchall()
print('Пользователи и их хэши паролей:')
for user in users:
    print(f'  ID: {user[0]}, Username: {user[1]}, Hash: {user[2][:50]}...')  # Показываем только начало хэша

conn.close()