import os
import sys
import logging
import shutil
import datetime
import time
from threading import Thread
from flask import Flask, flash, request, redirect, url_for, send_from_directory
from flask import render_template
from flask import current_app
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text #imported only for db.session.execute( text('select 1') )


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
    return render_template("index.html", data=content, title='Message In A Flask')

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
        io.emit("response_status")

@io.on('connect')
def connect():
    logging.info('client connected')
    _start_background_thread()

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
            messages = load_last_messages()
            send_to(messages, sid)
        except Exception as e:
            logging.exception(f'error loading records on user connected')
    
    if('user_name' in data and 'message' in data):
        try:
            message = Message(data['user_name'], data['message'])
            id = db.session.add(message)
            db.session.commit()
            data['id'] = id
            #io.emit('response', data, callback=messageReceived)
            send_to(message)
        except Exception as e:
            logging.exception(f'error saving record from data {data}')
        
def load_last_messages():
    messages = db.session.query(Message).order_by(Message.id.desc()).limit(10)
    messages=messages[::-1] #re-reverse    
    return messages

'''
send a single Message or a list of Message to one or more clients
default "all" clients
'''
def send_to(messages, clients='all'):
    if isinstance(messages, Message):
        messages = [messages]
    for message in messages:
        data = {'user_name':message.user, 'message':message.message, 'id':message.id}
        logging.debug(f'message to emit: {message} as {data} to {clients}')
        if clients == 'all':
            io.emit('response', data, callback=messageReceived)    
        else:
            if isinstance(clients, str):
                io.emit('response', data, callback=messageReceived, room=clients)

            if isinstance(clients, list):
                for client in clients:
                    io.emit('response', data, callback=messageReceived, room=client)


def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

def _start_background_thread():
    global thread
    if thread is None:
        thread = FlaskThread(target=_status_check)
        #thread = threading.Thread(target=_status_check)
        thread.daemon = True
        thread.start()
        logging.debug(f'thread status: {thread.is_alive} thread (new): {thread}')
    else:
        logging.debug(f'thread status: {thread.is_alive} thread: {thread}')

def _status_check():
    while True:
        data = {'db_connection': _get_connection_status(), 'client_count': _get_client_count()}
        if not isinstance( data['db_connection'], bool) or not isinstance( data['client_count'], int): 
            logging.error(f'emitting {data}')
        io.emit('server_status', data)
        time.sleep(5)

def _get_connection_status():
    error_connection_status = 'error with database connection'
    try:
        db.session.execute( text('select 1') )
        connection_status = True
    except Exception as e:
        logging.exception(error_connection_status)
        connection_status = error_connection_status
    return connection_status

def _get_client_count():
    error_client_count = 'error listing connected clients'
    try:
        client_count = len(clients)
    except Exception as e:
        logging.exception(error_client_count)
        client_count = error_client_count
    return client_count

class FlaskThread(Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = current_app._get_current_object()
        #logging.getLogger(__name__).debug(f'thread started')

    def run(self):
        with self.app.app_context():
            super().run()

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
    thread = None
    io.run(app, debug=True, host='0.0.0.0')

