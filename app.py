import os
import sys
import logging
import logging.handlers
import shutil
import datetime
import time
import uuid
import base64
import random
from threading import Thread
from flask import Flask, flash, request, redirect, url_for, send_from_directory
from flask import render_template
from flask import current_app
from flask import send_file
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.sql import text #imported only for db.session.execute( text('select 1') )
from dotenv import load_dotenv
load_dotenv()

clients = []
status = None
selected_song = None
status_thread = None
singer_thread = None

LOGS_FOLDER = './logs'
UPLOAD_FOLDER = './uploads'
SONGS_FOLDER = './songs'

COMMAND_SING = '//sing'

SONG_DELAY = 0.5    #seconds
CHECK_DELAY = 5     #seconds
ALLOWED_EXTENSIONS = set(['xlsx', 'txt', 'sh']) #NOT USED SHOULD BE CHANGED TO IMAGES


#logging.basicConfig(datefmt='%Y-%m-%d %H:%M:%S', filename='app.log', format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.DEBUG)
#logging.basicConfig(datefmt='%Y-%m-%d %H:%M:%S', format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.DEBUG, stream=sys.stdout)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chiave segreta ma non molto')    #usata da alcuni moduli quindi la creo anche se per ora non serve

#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@db/voices'
if not os.getenv('DB_CONN_STR'):
    logging.error(f'env variable DB_CONN_STR not set')
    exit(1)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_CONN_STR')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
migrate = Migrate(app, db)
io = SocketIO(app)


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
        logging.info('creating db')
        return 'db created'
    except:
        logging.exception('error creating db')
        return 'error creating db'

@app.route('/ping')
def ping():
    return 'Pong'

@app.route('/upload', methods=['POST'])
def upload_file():
    #TODO generate UUID for stored filename
    logging.debug(f'upload {request}')
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                return 'No file selected'
            file = request.files['file']
            if file.filename == '':
                return "No file selected"

            logging.debug(f'file: {file}')
            upload_file = uuid.uuid4().hex
            upload_path = os.path.join(UPLOAD_FOLDER, upload_file)
            file.save(upload_path)
            if os.path.exists(upload_path):
                status = f'file uploaded as {upload_path}'
                logging.debug(status)

                attachment = Attachment(file.filename, upload_file, None)
                db.session.add(attachment)
                db.session.commit()
            else:
                status = 'file not found'
                logging.warning(status)
            '''
            if file and allowed_file(file.filename):
                #file.save(secure_filename("file.xlsx"))  # saves in current directory
                file.save("file.xlsx")  # saves in current directory
                logging.debug(f'saving file {file.filename}')
                status = "File uploaded"
            else:
                logging.warning(f'invalid file {file.filename}')
            '''
            return upload_file
        except Exception as e:
            logging.exception(f'error saving file {file.filename}')
            return 'ERROR'

    return f'WRONG METHOD {request.method}'
    # return redirect(url_for('index'))

@app.route('/download/<file_id>', methods=['GET'])
def download(file_id):
    upload_path = os.path.join(UPLOAD_FOLDER, file_id)
    if os.path.exists(upload_path):
        #return send_file(upload_path)
        with open(upload_path, "rb") as image_file:
            b64_string = base64.b64encode(image_file.read())
            return b64_string


@io.on('get_status')
def get_status():
    if (status != None):
        logging.debug("Send status now")
        io.emit("response_status")

@io.on('connect')
def connect():
    logging.info('client connected')
    _start_background_status_thread()

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

        #send the last messages
        try:
            messages = load_last_messages(50)
            send_to(messages, sid)
        except Exception as e:
            logging.exception(f'error loading records on user connected')
    
    if('user_name' in data and 'message' in data):
        try:
            message = Message(data['user_name'], data['message'])
            db.session.add(message)
            db.session.commit()

            send_to(message)
            
            if data['message'] == COMMAND_SING:
                sing()
        except Exception as e:
            logging.exception(f'error saving record from data {data}')
        
    if('user_name' in data and 'upload_notification' in data):
        try:
            logging.debug(f'handling upload_notification {data}')
            stored_filename = data["upload_notification"]
            #message_content = f'<a class="btn" onclick="download(${stored_filename})">'
            message = Message(data['user_name'], message=None)           
            db.session.add(message)
            db.session.commit()

            attachment = Attachment.query.filter_by(stored_filename = stored_filename).first()
            attachment.message_id = message.id
            db.session.commit()
            logging.debug(f'assign message_id {message.id} to attachment {attachment}')
            logging.debug(f'message {message.attachments}')

            send_to(message)
        except Exception as e:
            logging.exception(f'error saving record from data {data}')        


def load_last_messages(quantity=10):
    messages = db.session.query(Message).order_by(Message.id.desc()).limit(quantity)
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
        if message.attachments:
            for attachment in message.attachments:
                if 'attachments' not in data:
                    data['attachments'] = []
                data['attachments'].append(attachment.stored_filename)
            
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
    
def sing():
    global selected_song
    #select new song
    entries = os.listdir(SONGS_FOLDER)
    songs = []
    for entry in entries:
        if entry.endswith('.txt'):
            songs.append(entry)
        
    selected_song = random.choice(songs)
    _start_background_singer_thread()
    pass
    
def _start_background_singer_thread():
    global singer_thread
    if singer_thread is None:
        singer_thread = FlaskThread(target=_sing)
        singer_thread.daemon = True
        singer_thread.start()
        logging.debug(f'singer_thread status: {singer_thread.is_alive()} thread (new): {singer_thread} with song {selected_song}')
    else:
        logging.debug(f'singer_thread status: {singer_thread.is_alive()} thread: {singer_thread} with song {selected_song}')
              

def _start_background_status_thread():
    global status_thread
    if status_thread is None:
        status_thread = FlaskThread(target=_status_check)
        #thread = threading.Thread(target=_status_check)
        status_thread.daemon = True
        status_thread.start()
        logging.debug(f'thread status: {status_thread.is_alive()} thread (new): {status_thread}')
    else:
        logging.debug(f'thread status: {status_thread.is_alive()} thread: {status_thread}')

def _sing():
    global selected_song
    lines = None
    last_line = 0
    band = None
    song_in_progress = False
    while True:
        try:
            if selected_song and not song_in_progress:
                logging.debug(f'loading song lines for {selected_song}')
                fh = open(os.path.join(SONGS_FOLDER, selected_song))
                lines = fh.readlines()
                last_line = 0
        except Exception as e:
            logging.exception(f'error reading song "{selected_song}"')

        if selected_song:
            if lines and last_line < len(lines):
                try:
                    song_in_progress = True
                    line = lines[last_line].strip()
                    #logging.debug(f'singing line {line}')
                    if len(line) > 0:
                        if last_line == 0:
                            band = line
                            last_line += 1
                            logging.info(f'starting song {selected_song}')
                            continue
                                                  
                        #create new Message
                        message = Message(band, line)
                        db.session.add(message)
                        db.session.commit()
                        send_to(message)  
                    last_line += 1
                except Exception as e:
                    logging.exception(f'error singing line {last_line}')
            else:
                logging.info(f'reached the end of song {selected_song}')
                lines = None
                selected_song = None
                song_in_progress = False
            
        time.sleep(SONG_DELAY)

def _status_check():
    while True:
        data = {'db_connection': _get_connection_status(), 'client_count': _get_client_count()}
        if not isinstance( data['db_connection'], bool) or not isinstance( data['client_count'], int): 
            logging.error(f'emitting {data}')
        io.emit('server_status', data)
        time.sleep(CHECK_DELAY)

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
    #attachments = db.relationship("Attachment", back_populates="message")
    attachments = db.relationship("Attachment", backref="message")
    ts = db.Column(db.DateTime)
    
    def __init__(self, user, message):
        self.user = user
        self.message = message
        self.ts = datetime.datetime.now()
    
class Attachment(db.Model):
    __tablenane__ = 'attachment'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    stored_filename = db.Column(db.String(255))
    ts = db.Column(db.DateTime)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=True)
    #message = db.relationship("Message", back_populates="attachment")
    
    def __init__(self, filename, stored_filename, message_id=None):
        self.filename = filename
        self.stored_filename = stored_filename
        self.message_id = message_id
        self.ts = datetime.datetime.now()

def get_configured_logger(name=None):
    logger = logging.getLogger(name)
    if (len(logger.handlers) == 0):
        # This logger has no handlers, so we can assume it hasn't yet been configured
        # Create RotatingFileHandler
        formatter = "%(asctime)s | %(levelname)s | %(process)s | %(thread)s | %(filename)s | %(funcName)s():%(lineno)d | %(message)s"
        handler = logging.handlers.RotatingFileHandler(os.path.join(LOGS_FOLDER,'app.log'), maxBytes = 1024*1024*10, backupCount = 6)
        handler.setFormatter(logging.Formatter(formatter))
        handler.setLevel(logging.INFO)
        
        handler_d = logging.handlers.RotatingFileHandler(os.path.join(LOGS_FOLDER,'app_debug.log'), maxBytes = 1024*1024*10, backupCount = 2)
        handler_d.setFormatter(logging.Formatter(formatter))
        handler_d.setLevel(logging.DEBUG)

        handler_c = logging.StreamHandler()
        handler_c.setFormatter(logging.Formatter(formatter))
        handler_c.setLevel(logging.DEBUG)          

        logger.addHandler(handler)
        logger.addHandler(handler_d)
        logger.addHandler(handler_c)
        logger.setLevel(logging.DEBUG)
    else:
        logging.info(f'logger {logger} already has {len(logger.handlers)}')

    return logger

get_configured_logger()

if __name__ == "__main__":
    #app.run("0.0.0.0", debug = True)
    thread = None
    io.run(app, debug=True, host='0.0.0.0')

