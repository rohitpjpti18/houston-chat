import os 
import secrets
import functools
import datetime, pytz
from PIL import Image
from flask_socketio import disconnect, join_room, leave_room
from flask import render_template, url_for, flash, redirect, request
from chat import app, db, bcrypt, socketio
from chat.models import User, ChatRoom, Room, Request, Message
from flask_login import login_user, current_user, logout_user, login_required
from chat.forms import RegistrationForm, LoginForm, UpdateAccountForm
import babel

def format_datetime(value, format='medium'):
    if format == 'full':
        format="EEEE, d. MMMM y 'at' HH:mm"
    elif format == 'medium':
        format="EE dd.MM.y HH:mm"
    return babel.dates.format_datetime(value, format)

app.jinja_env.filters['datetime'] = format_datetime



@app.route('/')
@login_required
def index():
    users = User.query.filter(~User.id.in_(db.session.query(ChatRoom.receiver_id).filter_by(sender_id=current_user.id))).all()
    return render_template("index.html", title='index', users=users)

@app.route('/home')
@login_required
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('index'))
    connections = ChatRoom.query.filter_by(sender_id=current_user.id).all()
    print(connections)
    return render_template("menu.html", title='home', connections=connections)


@app.route('/chat')
@login_required
def chat():
    receiver = User.query.filter_by(username=request.args.get('username')).first()
    print(request.args.get('username'))
    chatroom = ChatRoom.query.filter_by(sender_id=current_user.id, receiver_id=receiver.id).first()
    print(chatroom.room_id)
    messages = Message.query.filter_by(room_id=chatroom.room_id).all()
    return render_template('chatroom.html', chatroom=chatroom, messages=messages)



@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/send_request")
def create_request():
    send_to = User.query.filter_by(username=request.args.get('username')).first()
    connect_request = Request()
    connect_request.request_from_id = current_user.id
    connect_request.request_to_id = send_to.id
    print(Request.query.filter_by(request_from_id=current_user.id, request_to_id=send_to.id).first())
    if Request.query.filter_by(request_from_id=current_user.id, request_to_id=send_to.id).first() == None:
        db.session.add(connect_request)
        db.session.commit()
        flash(f'Your request to connect has been send to {send_to.username}.', 'success')
    return redirect(url_for('home'))
    

@app.route("/requests", methods=["GET", "POST"])
@login_required
def requests():
    if request.args.get('username'):
        print(request.args.get('username'))
        sender = User.query.filter_by(username=request.args.get('username')).first()
        
        new_room = Room()
        new_room.name = current_user.username + sender.username
        db.session.add(new_room)
        db.session.commit()
        get_new_room = Room.query.filter_by(name=current_user.username + sender.username).first()
        chatroom1, chatroom2 = ChatRoom(sender_id=current_user.id, receiver_id=sender.id, room_id = get_new_room.id), ChatRoom(sender_id=sender.id, receiver_id=current_user.id, room_id = get_new_room.id)
        db.session.add(chatroom1)
        db.session.add(chatroom2)
        db.session.commit()


        request_delete = Request.query.filter_by(request_to_id=current_user.id, request_from_id=sender.id).first()
        db.session.delete(request_delete)
        db.session.commit()

        flash('done', 'success')
        all_requests = Request.query.filter_by(request_to_id=current_user.id).all()
        print(all_requests)
        return render_template('request.html', requests=all_requests)
    
    all_requests =  Request.query.filter_by(request_to_id=current_user.id).all()
    print(all_requests)
    return render_template('request.html', requests=all_requests)
    



def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (300, 300)
    img = Image.open(form_picture)

    width, height = img.size
        #print(width, height)

    # check which one is smaller
    if height < width:
        # make square by cutting off equal amounts left and right
        left = (width - height) / 2
        right = (width + height) / 2
        top = 0
        bottom = height
        img = img.crop((left, top, right, bottom))
        img.thumbnail((300, 300))

    elif width < height:
        # make square by cutting from bottom
        left = 0
        right = width
        top = 0
        bottom = width
        img = img.crop((left, top, right, bottom))
        img.thumbnail((300, 300))
    img.thumbnail(output_size)
    img.save(picture_path)

    return picture_fn



@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.date_of_birth.data:
            current_user.date_of_birth = form.date_of_birth.data
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.email = form.email.data
        db.session.commit()
        flash('You account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.date_of_birth.data = current_user.date_of_birth
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)











def require_login(function):
    @functools.wraps(function)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return function(*args, **kwargs)
    return wrapped


@socketio.on('send_message')
@require_login
def send_message_handler(data):
    print(data['receiver'])
    receiver = User.query.filter_by(username=data['receiver']).first()
    chatroom = ChatRoom.query.filter_by(sender_id=current_user.id, receiver_id=receiver.id).first()
    tz = pytz.timezone('Asia/Kolkata')
    data['time'] = str(datetime.datetime.now(tz))
    message = Message(room_id=chatroom.room_id, sender_id=current_user.id, message=data['message'])
    db.session.add(message)
    db.session.commit()
    socketio.emit('receive_message', data, room=chatroom.room_id)


@socketio.on('join_room')
def join_room_handler(data):
    print(data['receiver'])
    receiver = User.query.filter_by(username=data['receiver']).first()
    chatroom = ChatRoom.query.filter_by(sender_id=current_user.id, receiver_id=receiver.id).first()
    join_room(chatroom.room_id)
    socketio.emit('join_room_announcement', data, room=chatroom.room_id)


@socketio.on('leave_room')
def leave_room_handler(data):
    print(data['receiver'])

    receiver = User.query.filter_by(username=data['receiver']).first()
    chatroom = ChatRoom.query.filter_by(sender_id=current_user.id, receiver_id=receiver.id).first()
    socketio.emit('leave_room_announcement', data, room=chatroom.room_id)


