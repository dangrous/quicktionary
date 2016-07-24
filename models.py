from peewee import *
import datetime

db = SqliteDatabase('games.db')

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    id = PrimaryKeyField()
    name = CharField()
    room_id = IntegerField(null=True)
    order_in_room = IntegerField(default=0)

class Room(BaseModel):
    id = PrimaryKeyField()
    code = CharField(unique=True)
    owner = ForeignKeyField(User, related_name='owner_of')
    leader = ForeignKeyField(User, related_name='leader_of', null=True)
    num_players = IntegerField(default=0)
    last_active = DateTimeField(default=datetime.datetime.now)
    # do I need this next one?
    show_subs = BooleanField(default=False)
    num_round = IntegerField(default=0)
    prompt = CharField(null=True)

class Submission(BaseModel):
    id = PrimaryKeyField()
    text = CharField()
    author = ForeignKeyField(User)
    room = ForeignKeyField(Room)
    show_auth = BooleanField(default=False)
    randomizer = FloatField()

def initialize_db():
    db.connect()
    db.create_tables([Submission, User, Room], safe=True)