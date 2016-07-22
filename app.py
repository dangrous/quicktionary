import json
import string
import random
from playhouse.shortcuts import model_to_dict, dict_to_model
from flask import Flask, Response, request, redirect, url_for, jsonify
from models import *

app = Flask(__name__, static_url_path='', static_folder='static')

@app.before_request
def before_request():
    initialize_db()

@app.teardown_request
def teardown_request(exception):
    db.close()

@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.route('/data', methods=['POST'])
def get_game_data():
    room = Room.get(Room.code == request.form['code'])
    users = User.select().where(User.room_id == room.id)
    return jsonify(gamedata=model_to_dict(room), players=[model_to_dict(user) for user in users])

@app.route('/connect', methods=['POST'])
def join_game():
    user = User.create(
        name=request.form['name']
    )
    if request.form['action'] == "start":
        # will need to check if it already exists.
        code = get_room_code()
        room = Room.create(
            code=code,
            owner=user
        )
        owner = True
    else:
        room = Room.get(Room.code == request.form['code'])
        owner = False
    # When many people joining quickly, this will not work I think.
    room.num_players += 1
    room.save()
    user.room_id = room.id
    # Because this won't match
    user.order_in_room = room.num_players
    user.save()
    users = User.select().where(User.room_id == room.id)
    return jsonify(players=[model_to_dict(user) for user in users], gamedata=model_to_dict(room), self=model_to_dict(user))

@app.route('/start', methods=['POST'])
def start_game():
    room = Room.get(Room.code == request.form['code'])
    first_player = User.get(User.room_id == room.id, User.order_in_room == random.randint(1, room.num_players))
    room.leader = first_player
    print room.leader.name
    room.num_round = 1
    room.save()
    return "Game started"

@app.route('/prompt', methods=['POST'])
def handle_prompts():
    room = Room.get(Room.code == request.form['code'])
    if request.form['action'] == 'clear':
        room.prompt = None
        room.save()
    elif request.form['action'] == 'set':
        room.prompt = request.form['prompt']
        room.save()
    return "Prompt updated"

def get_room_code():
    return ''.join(random.choice(string.ascii_uppercase) for n in range(5))

# need something to reveal individual submissions

# need something to randomize and reveal text of all submissions once round ready

# need something to change roles in round (I think just round leader)

if __name__ == '__main__':
    app.run(debug=True)