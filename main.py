import sqlite3

# Подключение к базе данных
conn = sqlite3.connect('films.db')
cur = conn.cursor()

# 1. Самый популярный фильм
cur.execute('SELECT title, budget FROM movies ORDER BY popularity DESC LIMIT 1')
most_popular = cur.fetchone()
print(f"Самый популярный фильм: {most_popular[0]}, Бюджет: {most_popular[1]}")

# 2. Самый дорогой фильм, вышедший в декабре 2009 года
cur.execute("""
    SELECT title FROM movies
    WHERE release_date LIKE '2009-12%' 
    ORDER BY budget DESC 
    LIMIT 1
""")
most_expensive_dec2009 = cur.fetchone()
print(f"Самый дорогой фильм декабря 2009 года: {most_expensive_dec2009[0]}")

# 3. Фильм со слоганом "The battle within."
cur.execute("SELECT title FROM movies WHERE tagline = 'The battle within.'")
battle_within = cur.fetchone()
print(f"Фильм со слоганом 'The battle within.': {battle_within[0]}")

# 4. Фильмы до 1980 года с рейтингом больше 8
cur.execute("""
    SELECT title, vote_count FROM movies
    WHERE release_date < '1980-01-01' AND vote_average > 8
    ORDER BY vote_count DESC
    LIMIT 1
""")
classic_hit = cur.fetchone()
print(f"Лучший фильм до 1980 с рейтингом > 8: {classic_hit[0]}, Голоса: {classic_hit[1]}")

conn.close()
