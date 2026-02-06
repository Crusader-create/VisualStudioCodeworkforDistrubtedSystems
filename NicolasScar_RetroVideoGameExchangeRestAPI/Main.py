# run by putting in terminal: docker compose up --build
#link is http://localhost:8080/docs

#I used ChatGPT to help with the new endpoints and the update to the docker-compose and nginx.conf.

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from database import users_collection, games_collection, trade_offers_collection
from bson import ObjectId
from fastapi import Body

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

class TradeOffer(BaseModel):
    from_user_email: str
    to_user_email: str
    offered_game_id: str
    requested_game_id: str
    status: str = "pending"

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
    


    #Trade offer endpoints
@app.post("/offers", status_code=201)
def create_offer(offer: TradeOffer):
    # Check that both users exist
    from_user = users_collection.find_one({"email": offer.from_user_email})
    to_user = users_collection.find_one({"email": offer.to_user_email})

    if not from_user or not to_user:
        raise HTTPException(status_code=404, detail="One or both users not found")

    # Check that offered game exists and belongs to sender
    offered_game = games_collection.find_one({"_id": ObjectId(offer.offered_game_id)})
    if not offered_game or offered_game["owner_email"] != offer.from_user_email:
        raise HTTPException(status_code=404, detail="Offered game not found or not owned by sender")

    # Check that requested game exists
    requested_game = games_collection.find_one({"_id": ObjectId(offer.requested_game_id)})
    if not requested_game:
        raise HTTPException(status_code=404, detail="Requested game not found")

    # Insert the offer into the database
    offer_dict = offer.dict()
    trade_offers_collection.insert_one(offer_dict)

    # Return HATEOAS links
    return {
        "message": "Trade offer created",
        "_links": {
            "self": {"href": "/offers"},
            "received_offers": {"href": f"/offers/received/{offer.to_user_email}"},
            "sent_offers": {"href": f"/offers/sent/{offer.from_user_email}"}
        }
    }

@app.get("/offers/received/{email}")
def get_received_offers(email: str):
    offers = []
    for offer in trade_offers_collection.find({"to_user_email": email}):
        offers.append(object_id_to_str(offer))
    return offers

@app.get("/offers/sent/{email}")
def get_sent_offers(email: str):
    offers = []
    for offer in trade_offers_collection.find({"from_user_email": email}):
        offers.append(object_id_to_str(offer))
    return offers

@app.put("/offers/{offer_id}")
def update_offer_status(offer_id: str, status: str):
    if status not in ["accepted", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    result = trade_offers_collection.update_one(
        {"_id": ObjectId(offer_id)},
        {"$set": {"status": status}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Offer not found")

    return {"message": f"Offer {status}"}

