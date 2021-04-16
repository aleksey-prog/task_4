import sqlite3 as sq
import telebot
from newsapi import NewsApiClient

conn = sq.connect('news_users.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE if NOT EXISTS "users" ("id" INTEGER NOT NULL UNIQUE, "user_id" INTEGER NOT NULL 
                    UNIQUE, PRIMARY KEY("id" AUTOINCREMENT));''')
cursor.execute('''CREATE TABLE if NOT EXISTS "categories" ("id" INTEGER NOT NULL UNIQUE, "user_id" INTEGER NOT NULL,
                    "news_categories" TEXT, PRIMARY KEY("id" AUTOINCREMENT));''')
cursor.execute('''CREATE TABLE if NOT EXISTS "keywords" ("id" INTEGER NOT NULL UNIQUE, "user_id" INTEGER NOT NULL,
                    "news_keywords" TEXT, PRIMARY KEY("id" AUTOINCREMENT));''')

conn.commit()
conn.close()

bot = telebot.TeleBot('TOKEN', parse_mode=None)  # Ввести токен
api = NewsApiClient(api_key='API_KEY')  # Ввести newsapi ключ

available_categories = ('business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology')


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, 'Бот для подписки на новости. Доступные команды - start, help, register, add_categories, '
                          'add_keywords, get_news_by_keyword, get_news_by_categories, delete_keywords, '
                          'delete_categories')


@bot.message_handler(commands=['register'])
def register_user(message):
    con = sq.connect('news_users.db')
    cur = con.cursor()
    try:
        cur.execute('''INSERT INTO users (user_id) VALUES (?)''', (message.from_user.id,))
        con.commit()
    except sq.IntegrityError:
        bot.reply_to(message, 'Пользователь уже зарегестрирован')

    con.close()


@bot.message_handler(commands=['add_keywords'])
def add_keyword(message):
    cid = message.chat.id
    news_keyword = bot.send_message(cid, 'Напишите тег для добавления (один за раз)')
    bot.register_next_step_handler(news_keyword, step_set_keyword)


def step_set_keyword(message):
    user_keyword = message.text
    con = sq.connect('news_users.db')
    cur = con.cursor()
    cur.execute('''INSERT INTO keywords (user_id, news_keywords) VALUES (?,?)''', (message.from_user.id, user_keyword,))
    con.commit()
    con.close()


@bot.message_handler(commands=['get_news_by_keyword'])
def news_get_by_keyword(message):
    cid = message.chat.id
    con = sq.connect('news_users.db')
    cur = con.cursor()
    cur.execute('''SELECT news_keywords FROM keywords WHERE user_id = (?)''', (message.from_user.id,))
    data = cur.fetchall()
    for n in data:
        all_articles = api.get_everything(q=n[0])
        bot.send_message(cid, '/----------------------/')
        bot.send_message(cid, f'Новости по теме: {n[0]}')
        bot.send_message(cid, '/----------------------/')
        for i in range(10):
            bot.send_message(cid, all_articles['articles'][i]['title'])
            bot.send_message(cid, all_articles['articles'][i]['url'])


@bot.message_handler(commands=['delete_keywords'])
def keyword_delete(message):
    cid = message.chat.id
    delete_keyword = bot.send_message(cid, 'Напишите тег для удаления (один за раз)')
    bot.register_next_step_handler(delete_keyword, step_keyword_delete)


def step_keyword_delete(message):
    keyword_text = message.text
    con = sq.connect('news_users.db')
    cur = con.cursor()
    cur.execute('''DELETE FROM keywords WHERE user_id = (?) AND news_keywords = (?)''', (message.from_user.id, keyword_text,))
    con.commit()
    con.close()


@bot.message_handler(commands=['add_categories'])
def add_category(message):
    cid = message.chat.id
    news_cat = bot.send_message(cid, 'Напишите категорию для добавления (одну за раз)')
    bot.register_next_step_handler(news_cat, step_set_category)


def step_set_category(message):
    cid = message.chat.id
    user_category = message.text
    if user_category in available_categories:
        con = sq.connect('news_users.db')
        cur = con.cursor()
        cur.execute('''INSERT INTO categories (user_id, news_categories) VALUES (?,?)''', (message.from_user.id, user_category,))
        con.commit()
        con.close()
    else:
        bot.send_message(cid, 'Для добавления доступны только категории: business, entertainment, general, health, '
                              'science, sports, technology')


@bot.message_handler(commands=['get_news_by_categories'])
def news_get_by_category(message):
    cid = message.chat.id
    con = sq.connect('news_users.db')
    cur = con.cursor()
    cur.execute('''SELECT news_categories FROM categories WHERE user_id = (?)''', (message.from_user.id,))
    data = cur.fetchall()
    for n in data:
        all_articles = api.get_top_headlines(category=n[0])
        bot.send_message(cid, '/----------------------/')
        bot.send_message(cid, f'Новости по категории: {n[0]}')
        bot.send_message(cid, '/----------------------/')
        for i in range(10):
            bot.send_message(cid, all_articles['articles'][i]['title'])
            bot.send_message(cid, all_articles['articles'][i]['url'])


@bot.message_handler(commands=['delete_categories'])
def category_delete(message):
    cid = message.chat.id
    delete_category = bot.send_message(cid, 'Напишите категорию для удаления (одну за раз)')
    bot.register_next_step_handler(delete_category, step_category_delete)


def step_category_delete(message):
    category_text = message.text
    con = sq.connect('news_users.db')
    cur = con.cursor()
    cur.execute('''DELETE FROM categories WHERE user_id = (?) AND news_categories = (?)''', (message.from_user.id, category_text,))
    con.commit()
    con.close()


bot.polling()
