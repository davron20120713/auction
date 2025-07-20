import sqlite3
from datetime import datetime
from config import DATABASE
import os
import cv2
import numpy as np
import random
from math import sqrt, ceil, floor

class DatabaseManager:
    def __init__(self, database):
        self.database = database

    def create_tables(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    user_name TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS prizes (
                    prize_id INTEGER PRIMARY KEY,
                    image TEXT,
                    used INTEGER DEFAULT 0
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS winners (
                    user_id INTEGER,
                    prize_id INTEGER,
                    win_time TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id),
                    FOREIGN KEY(prize_id) REFERENCES prizes(prize_id)
                )
            ''')

    def add_user(self, user_id, user_name):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute(
                'INSERT OR IGNORE INTO users (user_id, user_name) VALUES (?, ?)',
                (user_id, user_name)
            )

    def add_prize(self, data):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.executemany('INSERT INTO prizes (image) VALUES (?)', data)

    def add_winner(self, user_id, prize_id):
        win_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM winners WHERE user_id = ? AND prize_id = ?",
                (user_id, prize_id)
            )
            if cur.fetchone():
                return 0
            else:
                cur.execute(
                    'INSERT INTO winners (user_id, prize_id, win_time) VALUES (?, ?, ?)',
                    (user_id, prize_id, win_time)
                )
                conn.commit()
                return 1

    def mark_prize_used(self, prize_id):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('UPDATE prizes SET used = 1 WHERE prize_id = ?', (prize_id,))

    def get_users(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT user_id FROM users')
            return [x[0] for x in cur.fetchall()]

    def get_prize_img(self, prize_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT image FROM prizes WHERE prize_id = ?', (prize_id,))
            result = cur.fetchone()
            return result[0] if result else None

    def get_random_prize(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(
                'SELECT prize_id, image FROM prizes WHERE used = 0 ORDER BY RANDOM() LIMIT 1'
            )
            return cur.fetchone()

    def get_winners_count(self, prize_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) FROM winners WHERE prize_id = ?', (prize_id,))
            return cur.fetchone()[0]

    def get_rating(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT users.user_name, COUNT(*) as prize_count
                FROM winners
                JOIN users ON winners.user_id = users.user_id
                GROUP BY users.user_name
                ORDER BY prize_count DESC
                LIMIT 10
            ''')
            return cur.fetchall()

    def get_winners_img(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT image FROM winners 
                INNER JOIN prizes ON winners.prize_id = prizes.prize_id
                WHERE user_id = ?
            ''', (user_id,))
            return cur.fetchall()

def hide_img(img_name):
    image = cv2.imread(f'img/{img_name}')
    blurred_image = cv2.GaussianBlur(image, (15, 15), 0)
    pixelated_image = cv2.resize(blurred_image, (30, 30), interpolation=cv2.INTER_NEAREST)
    pixelated_image = cv2.resize(pixelated_image, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
    os.makedirs('hidden_img', exist_ok=True)
    cv2.imwrite(f'hidden_img/{img_name}', pixelated_image)

def create_collage(image_paths):
    images = []
    for path in image_paths:
        image = cv2.imread(path)
        images.append(image)

    num_images = len(images)
    num_cols = floor(sqrt(num_images))
    num_rows = ceil(num_images / num_cols)

    h, w = images[0].shape[:2]
    collage = np.zeros((num_rows * h, num_cols * w, 3), dtype=np.uint8)

    for i, image in enumerate(images):
        row = i // num_cols
        col = i % num_cols
        collage[row*h:(row+1)*h, col*w:(col+1)*w, :] = image

    return collage

if __name__ == '__main__':
    manager = DatabaseManager(DATABASE)
    manager.create_tables()

    prizes_img = os.listdir('img')
    data = [(x,) for x in prizes_img]

    conn = sqlite3.connect(DATABASE)
    existing = set(row[0] for row in conn.execute('SELECT image FROM prizes'))
    new_data = [d for d in data if d[0] not in existing]
    if new_data:
        manager.add_prize(new_data)

    for img in prizes_img:
        hide_img(img)
