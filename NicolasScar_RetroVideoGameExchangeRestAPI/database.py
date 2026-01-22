from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")

db = client["retro_game_exchange"]

users_collection = db["users"]
games_collection = db["games"]

