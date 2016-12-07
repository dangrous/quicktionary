import json
import urllib2
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
    submission_count = Submission.select().where(Submission.room == room, Submission.round_num == room.round_num).count()
    if submission_count > 0:
        if submission_count == room.num_players:
            submissions = Submission.select().where(Submission.room == room, Submission.round_num == room.round_num).order_by(Submission.randomizer)
        else:
            submissions = Submission.select().where(Submission.room == room, Submission.round_num == room.round_num)
        submissions = [model_to_dict(submission) for submission in submissions]
    else:
        submissions = ''
    vote_count = Vote.select().where(Vote.room == room, Vote.round_num == room.round_num).count()
    if vote_count > 0:
        votes = Vote.select().where(Vote.room == room, Vote.round_num == room.round_num)
    else:
        votes = ''
    return jsonify(gamedata=model_to_dict(room), submissions=submissions, players=[model_to_dict(player) for player in players], votes=[model_to_dict(vote) for vote in votes])

@app.route('/connect', methods=['POST'])
def join_game():
    if request.form['action'] == "start":
        player = Player.create(
            name=request.form['name']
        )
        code = get_room_code()
        while Room.select().where(Room.code == code).exists():
            code = get_room_code()
        room = Room.create(
            code=code,
            owner=player
        )
    else:
        try:
            room = Room.get(Room.code == request.form['code'])
        except:
            return jsonify(error="Sorry, we couldn't find that room. Please try again.")
        if Player.select().where(Player.name == request.form['name'], Player.room_id == room.id).exists():
            return jsonify(error="Sorry, someone has already joined with that name. Please try again.")
        else:
            player = Player.create(
                name=request.form['name']
            )
    # When many people joining quickly, this will not work I think.
    print "setting up shit"
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
    first_player.is_leader = True
    first_player.save()
    room.round_num = 1
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
        randomizer = random.random(),
        round_num = room.round_num
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
    room = Room.get(Room.id == request.form['room'])
    room.round_num = room.round_num + 1
    next_player = Player.get(Player.room_id == room.id, Player.order_in_room == room.leader.order_in_room % room.num_players + 1)
    room.leader.is_leader = False
    room.leader.save()
    room.leader = next_player
    next_player.is_leader = True
    room.prompt = None
    room.votes = 0
    room.save()
    next_player.save()
    players = Player.select().where(Player.room_id == room.id)
    for player in players:
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
    if author == room.leader and author != player:
        player.score += 1
    player.save()
    if author != room.leader and author != player:
        author.score += 1
    author.save()
    vote = Vote.create(
        room = room,
        voter = player,
        submission = submission,
        round_num = room.round_num
    )
    all_subs = Submission.select().where(Submission.room == room, Submission.round_num == room.round_num)
    vote_count = 0
    for submission in all_subs:
        vote_count += submission.votes
    if room.leader_can_vote:
        total_votes_needed = room.num_players
    else:
        total_votes_needed = room.num_players - 1
    if vote_count == total_votes_needed:
        for submission in all_subs:
            submission.show_auth = True
            submission.save()
    return jsonify(success=True)

def get_room_code():
    # more fun but fewer options - will need to delete old games if we do this, or add a recent option to all searches
    url = "http://randomword.setgetgo.com/get.php?len=" + str(random.randint(5,10))
    try: 
        randword = urllib2.urlopen(url, timeout=1).read().lower()
        return randword
    except:
        return ''.join(random.choice(string.ascii_lowercase) for n in range(6))

if __name__ == '__main__':
    app.run(debug=True)