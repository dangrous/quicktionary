from peewee import *
import datetime

db = SqliteDatabase('games.db')

class BaseModel(Model):
    class Meta:
        database = db

class Player(BaseModel):
    id = PrimaryKeyField()
    name = CharField()
    room_id = IntegerField(null=True)
    order_in_room = IntegerField(default=0)
    score = IntegerField(default=0)
    has_voted = BooleanField(default=False)

class Room(BaseModel):
    id = PrimaryKeyField()
    code = CharField(unique=True)
    owner = ForeignKeyField(Player, related_name='owner_of')
    leader = ForeignKeyField(Player, related_name='leader_of', null=True)
    num_players = IntegerField(default=0)
    last_active = DateTimeField(default=datetime.datetime.now)
    # do I need this next one?
    # show_subs = BooleanField(default=False)
    num_round = IntegerField(default=0)
    prompt = CharField(null=True)
    votes = IntegerField(default=0)

class Submission(BaseModel):
    id = PrimaryKeyField()
    text = CharField()
    author = ForeignKeyField(Player)
    room = ForeignKeyField(Room)
    show_auth = BooleanField(default=False)
    randomizer = FloatField()
    votes = IntegerField(default=0)

class Vote(BaseModel):
    id = PrimaryKeyField()
    room = ForeignKeyField(Room)
    voter = ForeignKeyField(Player, related_name='voted_for')
    submission = ForeignKeyField(Submission, related_name='vote_s')

def initialize_db():
    db.connect()
    db.create_tables([Submission, Player, Room], safe=True)