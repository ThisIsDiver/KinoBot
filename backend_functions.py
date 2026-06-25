import requests
import random
from peewee import (
    SqliteDatabase,
    Model,
    AutoField,
    IntegerField,
    TextField,
    DateTimeField,
)
from datetime import datetime


def movie_rating_getter(rating: dict):
    try:

        for key, value in rating.items():
            if value and key == "kp":
                result = value

        if result:
            return round(result, 2)
        else:
            return "Нет рейтинга"

    except UnboundLocalError:
        return "Нет рейтинга"


def movie_genres_getter(genres: list):
    result = str()
    first_genre = False

    for genre_obj in genres:
        for value in genre_obj.values():
            if first_genre == False:
                first_genre = True
                result += value.capitalize()
            else:
                result += f", {value}".title()

    return result


def search_movie(self, TOKENS):
    response = requests.get(
        f"https://api.kinopoisk.dev/v1.4/movie/search?query={self}",
        headers={"X-Api-Key": TOKENS["Kinopoisk TOKEN"]},
    )

    movie_docs = response.json()["docs"][0]

    result = {
        "name": (
            movie_docs["name"] if movie_docs["name"] else movie_docs["alternativeName"]
        ),
        "description": movie_docs["description"],
        "ratings": movie_rating_getter(movie_docs["rating"]),
        "year": movie_docs["year"],
        "genres": movie_genres_getter(movie_docs["genres"]),
        "ageRating": (
            movie_docs["ageRating"] if movie_docs["ageRating"] else "неизвестно"
        ),
        "poster": movie_docs["poster"]["url"],
    }

    return result


def top_movies_in_genre(self, TOKENS):
    response = requests.get(
        f"https://api.kinopoisk.dev/v1.4/movie?rating.kp=8.5-10&genres.name={self.lower()}",
        headers={"X-Api-Key": TOKENS["Kinopoisk TOKEN"]},
    )

    result = str()

    for i in range(0, 10):
        try:
            movie_docs = response.json()["docs"][i]
            result += f"{i+1}. {movie_docs["name"] if movie_docs["name"] else movie_docs["alternativeName"]} - {movie_rating_getter(movie_docs['rating'])} -- {movie_genres_getter(movie_docs['genres'])}\n"
        except IndexError:
            return "⚠️ОШИБКА⚠️\n\nОшибка в названии жанра"

    return result


def search_movie_genre(self, TOKENS):
    try:
        response = requests.get(
            f"https://api.kinopoisk.dev/v1.4/movie/random?genres.name={self.lower()}&rating.kp={random.uniform(5.5, 9.2)}-10",
            headers={"X-Api-Key": TOKENS["Kinopoisk TOKEN"]},
        )

        movie_docs = response.json()

        result = {
            "name": (
                movie_docs["name"]
                if movie_docs["name"]
                else movie_docs["alternativeName"]
            ),
            "description": movie_docs["description"],
            "ratings": movie_rating_getter(movie_docs["rating"]),
            "year": movie_docs["year"],
            "genres": movie_genres_getter(movie_docs["genres"]),
            "ageRating": (
                movie_docs["ageRating"] if movie_docs["ageRating"] else "неизвестно"
            ),
            "poster": movie_docs["poster"]["url"],
        }

        return result
    except TypeError:
        return False


# База данных

db = SqliteDatabase("history.db")


class DataModel(Model):
    class Meta:
        database = db


class History(DataModel):
    id = AutoField()
    user_id = IntegerField()
    name = TextField()
    description = TextField()
    rating = TextField()
    year = TextField()
    genres = TextField()
    ageRating = TextField()
    poster = TextField()
    created_at = DateTimeField(default=datetime.now)


db.connect()
db.create_tables([History])
print("База данных запущена")
