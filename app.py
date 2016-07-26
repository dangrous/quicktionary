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
    room = Room.get(Room.id == request.form['room'])
    players = Player.select().where(Player.room_id == room.id)
    submission_count = Submission.select().where(Submission.room == room).count()
    if submission_count > 0:
        if submission_count == room.num_players:
            submissions = Submission.select().where(Submission.room == room).order_by(Submission.randomizer)
        else:
            submissions = Submission.select().where(Submission.room == room)
        submissions = [model_to_dict(submission) for submission in submissions]
    else:
        submissions = ''
    return jsonify(gamedata=model_to_dict(room), submissions=submissions, players=[model_to_dict(player) for player in players])

@app.route('/connect', methods=['POST'])
def join_game():
    player = Player.create(
        name=request.form['name']
    )
    if request.form['action'] == "start":
        # will need to check if it already exists.
        code = get_room_code()
        room = Room.create(
            code=code,
            owner=player
        )
        owner = True
    else:
        room = Room.get(Room.code == request.form['code'])
        owner = False
    # When many people joining quickly, this will not work I think.
    room.num_players += 1
    room.save()
    player.room_id = room.id
    # Because this won't match
    player.order_in_room = room.num_players
    player.save()
    players = Player.select().where(Player.room_id == room.id)
    return jsonify(players=[model_to_dict(player) for player in players], gamedata=model_to_dict(room), self=model_to_dict(player))

@app.route('/start', methods=['POST'])
def start_game():
    room = Room.get(Room.id == request.form['room'])
    first_player = Player.get(Player.room_id == room.id, Player.order_in_room == random.randint(1, room.num_players))
    room.leader = first_player
    room.num_round = 1
    room.save()
    return "Game started"

@app.route('/prompt', methods=['POST'])
def handle_prompts():
    room = Room.get(Room.id == request.form['room'])
    if request.form['action'] == 'clear':
        room.prompt = None
        room.save()
    elif request.form['action'] == 'set':
        room.prompt = request.form['prompt']
        room.save()
    return "Prompt updated"

@app.route('/submit', methods=['POST'])
def handle_submissions():
    room = Room.get(Room.id == request.form['room'])
    player = Player.get(Player.id == request.form['self'])
    submission = Submission.create(
        text = request.form['submission'],
        author = player,
        room = room,
        randomizer = random.random()
    )
    return "Submission added"

@app.route('/reveal', methods=['POST'])
def reveal_submission():
    submission = Submission.get(Submission.id == request.form['submission'])
    submission.show_auth = True
    submission.save()
    return "Submission revealed."

@app.route('/advance', methods=['POST'])
def advance_round():
    delete_subs = Submission.delete().where(Submission.room_id == request.form['room'])
    delete_subs.execute()
    room = Room.get(Room.id == request.form['room'])
    room.num_round = room.num_round + 1
    next_player = Player.get(Player.room_id == room.id, Player.order_in_room == room.leader.order_in_room % room.num_players + 1)
    room.leader = next_player
    room.prompt = None
    room.votes = 0
    room.save()
    players = Player.select().where(Player.room_id == room.id)
    for player in playerss:
        player.has_voted = False
        player.save()
    return "Begun next round."

@app.route('/vote', methods=['POST'])
def vote():
    submission = Submission.get(Submission.id == request.form['submission'])
    submission.votes += 1
    submission.save()
    room = submission.room
    room.votes += 1
    room.save()
    author = submission.author
    player = Player.get(Player.id == request.form['player'])
    player.has_voted = True
    if not author == room.leader:
        author.score += 1
    else:
        player.score += 1
    author.save()
    player.save()
    vote = Vote.create(
        room = room,
        voter = player,
        submission = submission
    )
    all_subs = Submission.select().where(Submission.room == room)
    vote_count = 0
    for submission in all_subs:
        vote_count += submission.votes
    if vote_count == room.num_players:
        for submission in all_subs:
            submission.show_auth = True
            submission.save()
    return "vote counted"

def get_room_code():
    return ''.join(random.choice(string.ascii_uppercase) for n in range(5))

if __name__ == '__main__':
    app.run(debug=True)