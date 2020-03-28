from datetime import datetime
from chat import db, login_manager
from flask_login import UserMixin
import pytz

tz = pytz.timezone('Asia/Kolkata')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    first_name = db.Column(db.String(20), nullable=True, unique=False)
    last_name = db.Column(db.String(20), nullable=True, unique=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self): 
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=True)
    
    def __repr__(self): 
        return f"Room('{self.id}', '{self.name}')"

class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    receiver = db.relationship("User", foreign_keys="[ChatRoom.receiver_id]")
    sender = db.relationship("User", foreign_keys="[ChatRoom.receiver_id]")

    def __repr__(self): 
        return f"ChatRoom('{self.id}', '{self.sender_id}', '{self.room_id}')"

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_sent = db.Column(db.DateTime, nullable=False, default=datetime.now(tz))
    message = db.Column(db.Text, nullable=False)
    sender = db.relationship("User", foreign_keys="[Message.sender_id]")

    def __repr__(self): 
        return f"Message('{self.id}', '{self.message}' )"


class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_from_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    request_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    request_from = db.relationship("User", foreign_keys="[Request.request_from_id]")
    request_to = db.relationship("User", foreign_keys="[Request.request_to_id]")

    def __repr__(self): 
        return f"Request('{self.id}', '{self.request_from_id}')"