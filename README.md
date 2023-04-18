# msg_in_a_flask
small flask chat demo using gunicorn and flask_socketio


deploy with an environment variable 
DB_CONN_STR=postgresql+psycopg2://user:pass@host:5432/mydatabase

or 
DB_CONN_STR=mysql+pymysql://user:pass@host/mydatabase



example setup for mysql
CREATE DATABASE `msg_in_a_flask`;
CREATE USER 'msg_user'@'localhost' IDENTIFIED BY 'msg_pass';
GRANT USAGE ON *.* TO 'msg_user'@'localhost';
GRANT ALL  ON `msg_in_a_flask`.* TO 'msg_user'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;

for cmd
set DB_CONN_STR=mysql+pymysql://msg_user:msg_pass@localhost/msg_in_a_flask

for ps
$env:DB_CONN_STR='mysql+pymysql://msg_user:msg_pass@localhost/msg_in_a_flask'

then run the application
python app.py