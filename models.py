from peewee import *
import datetime

db = SqliteDatabase('games.db')

class BaseModel(Model):
    class Meta:
        database = db
    date_created = DateTimeField(default=datetime.datetime.now)
    id = PrimaryKeyField()

class Player(BaseModel):
    name = CharField()
    room_id = IntegerField(null=True)
    order_in_room = IntegerField(default=0)
    score = IntegerField(default=0)
    has_voted = BooleanField(default=False)
    is_leader = BooleanField(default=False)

class Room(BaseModel):
    code = CharField(unique=True)
    owner = ForeignKeyField(Player, related_name='owner_of')
    leader = ForeignKeyField(Player, related_name='leader_of', null=True)
    num_players = IntegerField(default=0)
    round_num = IntegerField(default=0)
    prompt = CharField(null=True)
    votes = IntegerField(default=0)
    # Game Characteristics
    # EASY
    leader_can_vote = BooleanField(default=False)
    can_vote_for_self = BooleanField(default=False)
    # FOR LATER
    sub_can_be_revealed = BooleanField(default=False)
    guess_player = BooleanField(default=False)
    play_until = IntegerField(null=True)
    rounds_or_score = BooleanField(default=False) # False is round limit, True is score limit
    vote_points = IntegerField(default=1)
    voted_points = IntegerField(default=1)

class Submission(BaseModel):
    text = CharField()
    author = ForeignKeyField(Player)
    room = ForeignKeyField(Room)
    show_auth = BooleanField(default=False)
    randomizer = FloatField()
    votes = IntegerField(default=0)
    round_num = IntegerField()

class Vote(BaseModel):
    room = ForeignKeyField(Room)
    voter = ForeignKeyField(Player, related_name='voted_for')
    submission = ForeignKeyField(Submission, related_name='voted_for_by')
    round_num = IntegerField()
    player_guess = ForeignKeyField(Player, related_name='guessed', null=True)

def initialize_db():
    db.connect()
    db.create_tables([Player, Room, Submission, Vote], safe=True)