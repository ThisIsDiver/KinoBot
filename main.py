import peewee
import telebot
import backend_functions
import json
import requests


def check_tokens(TOKENS):
    print("\nПроверка токена Kinopoisk API")
    response = requests.get(
        f"https://api.kinopoisk.dev/v1.4/movie/search?query=Терминатор",
        headers={"X-Api-Key": TOKENS["Kinopoisk TOKEN"]},
    )
    if response:
        pass
    else:
        print(f"\033[91mОшибка с токеном Kinopoisk API: {response}\033[0m")
        raise SystemExit(1)
    try:
        print("\nПроверка токена Telegram API")
        telebot.TeleBot(TOKENS["TG-TOKEN"]).get_me()
    except Exception as exception:
        print(
            f"\033[91mОшибка c токеном. Проверьте правильность или подключение к Telegram API. Ошибка: {exception}\033[0m"
        )
        raise SystemExit(1)
    return "\n\033[92mВсё отлично, бот запущен\033[0m"


TOKENS = False
with open("config.json", "r", encoding="utf-8") as token:
    TOKENS = json.load(token)

print(check_tokens(TOKENS))

bot = telebot.TeleBot(TOKENS["TG-TOKEN"])


# Странно, что тут у меня копируются смайлики в изображении, а не как в Дискорде :smile:. Какая-то особенность с ТГ?
def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton("🔍 Поиск фильма/сериала по названию")
    btn2 = telebot.types.KeyboardButton(
        "💥 10 случайных топовых фильмов/сериалов в жанре"
    )
    btn3 = telebot.types.KeyboardButton("🎲 Случайный фильм по жанру")
    btn4 = telebot.types.KeyboardButton("📜 История запросов")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    return markup


@bot.message_handler(commands=["start"])
def start(message):
    text = f"Привет, {message.from_user.first_name}! 🎬\n\nВыберите одно из действий в меню 👇"
    bot.send_message(message.chat.id, text, reply_markup=main_menu())


@bot.message_handler(commands=["history"])
def show_history(message):
    history = (
        backend_functions.History.select()
        .where(backend_functions.History.user_id == message.from_user.id)
        .order_by(backend_functions.History.created_at.desc())
        .limit(15)
    )

    if not history:
        bot.send_message(message.chat.id, "История пуста 📭")
        return

    text = "📜 Последние запросы:\n\n"
    bot.send_message(message.chat.id, text)
    for item in history:
        try:
            text = f"{item.created_at.strftime('%d.%m.%Y %H:%M')}\n\n🎬 {item.name}\n\nОписание:\n{item.description}\n\nРейтинг на Кинопоиске: {item.rating}\n\nГод производства: {item.year}\n\nЖанры: {item.genres}\n\nВозрастной рейтинг: {item.ageRating}\n"
            if item.poster:
                bot.send_photo(message.chat.id, item.poster, caption=text)
            else:
                bot.send_message(message.chat.id, text)

        except telebot.apihelper.ApiTelegramException:
            text_1 = f"{item.name}\n\nОписание:\n{item.description}"
            text_2 = f"Рейтинг на Кинопоиске: {item.rating}\n\nГод производства: {item.year}\n\nЖанры: {item.genres}\n\nВозрастной рейтинг: {item.ageRating}"
            if item.poster:
                bot.send_photo(message.chat.id, item.poster, caption=text_1)
                bot.send_message(message.chat.id, text_2)
            else:
                bot.send_message(message.chat.id, text_1)
                bot.send_message(message.chat.id, text_2)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "🔍 Поиск фильма/сериала по названию":
        msg = bot.send_message(message.chat.id, "Введите название фильма 🎥")
        bot.register_next_step_handler(msg, lambda m: process_search_name(m, TOKENS))
    elif message.text == "💥 10 случайных топовых фильмов/сериалов в жанре":
        msg = bot.send_message(message.chat.id, "Введите название жанра 🎥")
        bot.register_next_step_handler(msg, lambda m: process_top_in_genre(m, TOKENS))
    elif message.text == "🎲 Случайный фильм по жанру":
        msg = bot.send_message(message.chat.id, "Введите название жанра 🎥")
        bot.register_next_step_handler(msg, lambda m: process_search_genre(m, TOKENS))
    elif message.text == "📜 История запросов":
        show_history(message)
    else:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        back_btn = telebot.types.KeyboardButton("/start")
        markup.add(back_btn)
        bot.send_message(
            message.chat.id,
            "Не понял команду 🤔\nНажми кнопку ниже, чтобы открыть меню 👇",
            reply_markup=markup,
        )


def process_search_name(message, TOKENS):
    query = message.text
    result = backend_functions.search_movie(query, TOKENS)

    if "error" in result:
        bot.send_message(message.chat.id, result["error"])
        return

    name = result["name"]
    description = result["description"]
    ratings = result["ratings"]
    year = result["year"]
    genres = result["genres"]
    ageRating = result["ageRating"]
    poster = result["poster"]

    text = f"🎬 {name}\n\nОписание:\n{description}\n\nРейтинг на Кинопоиске: {ratings}\n\nГод производства: {year}\n\nЖанры: {genres}\n\nВозрастной рейтинг: {ageRating}"

    try:
        if poster:
            bot.send_photo(message.chat.id, poster, caption=text)
        else:
            bot.send_message(message.chat.id, text)

    except telebot.apihelper.ApiTelegramException:
        text_1 = f"{name}\n\nОписание:\n{description}"
        text_2 = f"Рейтинг на Кинопоиске: {ratings}\n\nГод производства: {year}\n\nЖанры: {genres}\n\nВозрастной рейтинг: {ageRating}"
        if poster:
            bot.send_photo(message.chat.id, poster, caption=text_1)
            bot.send_message(message.chat.id, text_2)
        else:
            bot.send_message(message.chat.id, text_1)
            bot.send_message(message.chat.id, text_2)

    backend_functions.History.create(
        user_id=message.from_user.id,
        name=name,
        description=description,
        rating=ratings,
        year=year,
        genres=genres,
        ageRating=ageRating,
        poster=poster,
    )


def process_top_in_genre(message, TOKENS):
    query = message.text
    result = backend_functions.top_movies_in_genre(query, TOKENS)

    if "error" in result:
        bot.send_message(message.chat.id, result["error"])
        return

    text = f"🎬 Случайный список фильмов и сериалов в жанре с рейтингами от 8 до 10: {query}:\n{result}"

    bot.send_message(message.chat.id, text)


def process_search_genre(message, TOKENS):
    query = message.text
    result = backend_functions.search_movie_genre(query, TOKENS)

    if result:

        if "error" in result:
            bot.send_message(message.chat.id, result["error"])
            return

        name = result["name"]
        description = result["description"]
        ratings = result["ratings"]
        year = result["year"]
        genres = result["genres"]
        ageRating = result["ageRating"]
        poster = result["poster"]

        text = f"🎬 {name}\n\nОписание:\n{description}\n\nРейтинг на Кинопоиске: {ratings}\n\nГод производства: {year}\n\nЖанры: {genres}\n\nВозрастной рейтинг: {ageRating}"

        try:
            backend_functions.History.create(
                user_id=message.from_user.id,
                name=name,
                description=description,
                rating=ratings,
                year=year,
                genres=genres,
                ageRating=ageRating,
                poster=poster,
            )
        except peewee.IntegrityError:
            process_search_genre(message, TOKENS)
            return
        try:
            if poster:
                bot.send_photo(message.chat.id, poster, caption=text)
            else:
                bot.send_message(message.chat.id, text)

        except telebot.apihelper.ApiTelegramException:
            text_1 = f"{name}\n\nОписание:\n{description}"
            text_2 = f"Рейтинг на Кинопоиске: {ratings}\n\nГод производства: {year}\n\nЖанры: {genres}\n\nВозрастной рейтинг: {ageRating}"
            if poster:
                bot.send_photo(message.chat.id, poster, caption=text_1)
                bot.send_message(message.chat.id, text_2)
            else:
                bot.send_message(message.chat.id, text_1)
                bot.send_message(message.chat.id, text_2)
    else:
        bot.send_message(
            message.chat.id,
            "⚠️ ERROR: Ошибка либо в названии жанра, либо на стороне Kinopoisk. Попробуйте ещё раз",
        )


if __name__ == "__main__":
    print("Бот запущен")
    bot.infinity_polling()
