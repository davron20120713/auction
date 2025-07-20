from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from logic import *
import schedule
import threading
import time
from config import *

bot = TeleBot(API_TOKEN)
manager = DatabaseManager(DATABASE)
manager.create_tables()

def gen_markup(prize_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Получить!", callback_data=str(prize_id)))
    return markup

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    username = message.from_user.username or "noname"
    if user_id in manager.get_users():
        bot.reply_to(message, "Ты уже зарегистрирован!")
    else:
        manager.add_user(user_id, username)
        bot.reply_to(message, """Привет! Ты успешно зарегистрирован! 🎉

Каждый час тебе будут приходить новые картинки. У тебя будет шанс их получить, если ты нажмешь на кнопку 'Получить!' быстрее других.

⚠️ Только первые 3 пользователя получат приз!""")

@bot.message_handler(commands=['rating'])
def handle_rating(message):
    res = manager.get_rating()
    if not res:
        bot.send_message(message.chat.id, "Рейтинг пока пуст.")
        return

    lines = [f'| @{x[0]:<11} | {x[1]:<11}|\n{"_"*26}' for x in res]
    header = f'| USER_NAME   | COUNT_PRIZE|\n{"_"*26}'
    table = header + '\n' + '\n'.join(lines)
    bot.send_message(message.chat.id, table)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    prize_id = int(call.data)
    user_id = call.message.chat.id
    username = call.from_user.username or "noname"

    manager.add_user(user_id, username)

    if manager.get_winners_count(prize_id) < 3:
        if manager.add_winner(user_id, prize_id):
            img = manager.get_prize_img(prize_id)
            if img:
                with open(f'img/{img}', 'rb') as photo:
                    bot.send_photo(user_id, photo, caption="🎉 Поздравляем! Ты получил приз!")
            else:
                bot.send_message(user_id, "Ошибка: не удалось найти изображение.")
        else:
            bot.send_message(user_id, "❗ Ты уже получал этот приз.")
    else:
        bot.send_message(user_id, "😔 Этот приз уже забрали 3 человека.")

def send_message():
    prize = manager.get_random_prize()
    if not prize:
        print("Нет доступных призов.")
        return

    prize_id, img = prize
    manager.mark_prize_used(prize_id)
    hide_img(img)

    for user in manager.get_users():
        try:
            with open(f'hidden_img/{img}', 'rb') as photo:
                bot.send_photo(user, photo, reply_markup=gen_markup(prize_id))
        except Exception as e:
            print(f"Ошибка при отправке: {e}")

def schedule_thread():
    schedule.every(1).hours.do(send_message)  # меняй на every(30).seconds для тестов
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_bot():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    thread_bot = threading.Thread(target=start_bot)
    thread_sched = threading.Thread(target=schedule_thread)

    thread_bot.start()
    thread_sched.start()
