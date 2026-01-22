# this is how ya run the project. I didn't know if i needed to put this or not but i assume i might need to since everyone will likely do something different.
# pip install -r requirements.txt
# python -m uvicorn main:app --reload
# below is the link to see the documentation and you can test the endpoints there as well
# http://127.0.0.1:8000/docs

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from database import users_collection, games_collection
from bson import ObjectId

app = FastAPI(title="Retro Video Game Exchange")

def object_id_to_str(item):
    item["_id"] = str(item["_id"])
    return item

class User(BaseModel):
    name: str
    email: str
    password: str
    address: str

class UserUpdate(BaseModel):
    name: Optional[str]
    address: Optional[str]

class Game(BaseModel):
    name: str
    publisher: str
    year_published: int
    system: str
    condition: str
    previous_owners: Optional[int] = None
    owner_email: str

# user endpoints
@app.post("/users", status_code=201)
def create_user(user: User):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    users_collection.insert_one(user.dict())
    return {
        "message": "User created",
        "_links": {
            "self": {"href": "/users"},
            "add_game": {"href": "/games"}
        }
    }

@app.get("/users/{email}")
def get_user(email: str):
    user = users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.pop("password")
    return object_id_to_str(user)

@app.put("/users/{email}")
def update_user(email: str, update: UserUpdate):
    result = users_collection.update_one(
        {"email": email},
        {"$set": update.dict(exclude_none=True)}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User updated"}

# game endpoints 
@app.post("/games", status_code=201)
def add_game(game: Game):
    games_collection.insert_one(game.dict())
    return {
        "message": "Game added",
        "_links": {
            "self": {"href": "/games"},
            "owner_games": {"href": f"/games/owner/{game.owner_email}"}
        }
    }

@app.get("/games", response_model=List[dict])
def get_all_games():
    games = []
    for game in games_collection.find():
        games.append(object_id_to_str(game))
    return games

@app.get("/games/owner/{email}")
def get_games_by_owner(email: str):
    games = []
    for game in games_collection.find({"owner_email": email}):
        games.append(object_id_to_str(game))
    return games

@app.get("/games/search")
def search_games(name: str):
    games = []
    for game in games_collection.find({"name": {"$regex": name, "$options": "i"}}):
        games.append(object_id_to_str(game))
    return games

@app.put("/games/{game_id}")
def update_game(game_id: str, game: Game):
    result = games_collection.update_one(
        {"_id": ObjectId(game_id)},
        {"$set": game.dict()}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Game not found")
    return {"message": "Game updated"}

@app.delete("/games/{game_id}", status_code=204)
def delete_game(game_id: str):
    result = games_collection.delete_one({"_id": ObjectId(game_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Game not found")
