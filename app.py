import os
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
    return app.send_static_file('index_temp.html')

# should update to actually call a database at some point but for now it's okay
@app.route('/api/submissions', methods=['GET', 'POST'])
def submissions_handler():
    return "SUP"
    # submissions = []
    # for submission in Submission.select():
    #     submissions.append(model_to_dict(submission))

    # return Response(
    #     json.dumps(submissions),
    #     mimetype='application/json',
    #     headers={
    #         'Cache-Control': 'no-cache',
    #         'Access-Control-Allow-Origin': '*'
    #     }
    # )

@app.route('/testing')
def test_add_submission():
    Submission.create(
        text = "This is a great submission",
        author = 1,
        room = 1
    )

    return "Submission added"

# check user's permissions - can they do what they're trying to do?
@app.route('/api/permissions')
def check_permissions():
    pass

# set up the users, temporarily
@app.route('/api/games', methods=['POST'])
def join_game():
    if request.form['action'] == "update":
        room = Room.get(Room.code == request.form['code'])
        users = User.select().where(User.room_id == room.id)
        return jsonify(users=[model_to_dict(user) for user in users], room=room.code)

    else:

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

        return jsonify(users=[model_to_dict(user) for user in users], room=room.code, owner=owner, self=model_to_dict(user))

@app.route('/newround', methods=['POST'])
def start_round():
    pass

@app.route('/started', methods=['POST'])
def has_game_started():
    room = Room.get(Room.code == request.form['code'])
    return jsonify(started=room.num_round > 0, info=model_to_dict(room))

@app.route('/startgame', methods=['POST'])
def start_game():
    room = Room.get(Room.code == request.form['code'])
    first_player = User.get(User.room_id == room.id, User.order_in_room == random.randint(1, room.num_players))
    room.leader = first_player
    room.num_round = 1
    room.save()
    return "Game started"

# This should consolidate all other update operations
@app.route('/gamedata', methods=['POST'])
def get_game_data():
    room = Room.get(Room.code == request.form['code'])
    users = User.select().where(User.room_id == room.id)
    return jsonify(data=model_to_dict(room), players=model_to_dict(users))

@app.route('/leader', methods=['POST'])
def get_round_leader():
    room = Room.get(Room.code == request.form['code'])
    return jsonify(leader=model_to_dict(room.leader))

@app.route('/prompt', methods=['POST'])
def handle_prompts():
    room = Room.get(Room.code == request.form['code'])
    if request.form['action'] == 'clear':
        room.prompt = None
        room.save()
    elif request.form['action'] == 'get':
        # return a json version of the prompt.
        pass
    elif request.form['action'] == 'set':
        room.prompt = request.form['prompt']
        room.save()

def get_room_code():
    return ''.join(random.choice(string.ascii_uppercase) for n in range(5))

# need something to reveal individual submissions

# need something to randomize and reveal text of all submissions once round ready

# need something to change roles in round (I think just round leader)

if __name__ == '__main__':
    app.run(debug=True)