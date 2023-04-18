import os
import sys
import logging
import shutil
import datetime
from flask import Flask, flash, request, redirect, url_for, send_from_directory
from flask import render_template
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy

status = None

#logging.basicConfig(datefmt='%Y-%m-%d %H:%M:%S', filename='app.log', format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.DEBUG)

logging.basicConfig(datefmt='%Y-%m-%d %H:%M:%S', format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.DEBUG, stream=sys.stdout)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chiave segreta ma non molto'    #usata da alcuni moduli quindi la creo anche se per ora non serve

#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@db/voices'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_CONN_STR')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

io = SocketIO(app)
clients = []

@app.route('/')
def home():
    return redirect(url_for('index'))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/index')
def index():
    try:
        db.create_all()
    except:
        logging.exception('error creating db')
    content = ''
    return render_template("index.html", data=content, title='Mypage - index')


@app.route('/create')
def create():
    try:
        db.create_all()
        return 'db created'
    except:
        logging.exception('error creating db')
        return 'error creating db'

@app.route('/ping')
def ping():
    return 'Pong'

@io.on('get_status')
def get_status():
    if (status != None):
        logging.debug("Send status now")
        emit("response_status")

@io.on('disconnect')
def disconnect():
    sid = request.sid
    logging.info(f'disconnected {sid}')
    clients.remove(sid)

@io.on('data_event')
def handle_data_event(data, methods=['GET', 'POST']):
    print('received data_event: ' + str(data))

    if('data' in data and data['data']=='user connected'):
        #save new client
        sid = request.sid
        clients.append(sid)

        #send the last 10 messages
        try:
            messages = db.session.query(Message).order_by(Message.id.desc()).limit(10)
            messages=messages[::-1] #re-reverse
            sendMessagesToClient(messages, sid)
        except Exception as e:
            logging.exception(f'error loading records on user connected')
    
    if('user_name' in data and 'message' in data):
        try:
            message = Message(data['user_name'], data['message'])
            id = db.session.add(message)
            db.session.commit()
            data['id'] = id
            #io.emit('response', data, callback=messageReceived)
            sendMessageToEveryone(message)
        except Exception as e:
            logging.exception(f'error saving record from data {data}')
        

def sendMessagesToClient(messages, client):
    for message in messages:
        data = {'user_name':message.user, 'message':message.message, 'id':message.id}
        logging.debug(f'message to emit: {message} as {data} to {client}')
        io.emit('response', data, callback=messageReceived, room=client)

def sendMessageToEveryone(message):
    data = {'user_name':message.user, 'message':message.message, 'id':message.id}
    logging.debug(f'message to emit: {message} as {data}')
    io.emit('response', data, callback=messageReceived)    


def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')


class Message(db.Model):
    __tablenane__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(255))
    message = db.Column(db.String(255))
    ts = db.Column(db.DateTime)
    
    def __init__(self, user, message):
        self.user = user
        self.message = message
        self.ts = datetime.datetime.now()
    

if __name__ == "__main__":
    #app.run("0.0.0.0", debug = True)
    io.run(app, debug=True, host='0.0.0.0')

