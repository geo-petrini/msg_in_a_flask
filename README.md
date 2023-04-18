# msg_in_a_flask
small flask chat demo using gunicorn and flask_socketio


deploy with an environment variable 
DB_CONN_STR=postgresql+psycopg2://user:pass@host:5432/mydatabase

or 
DB_CONN_STR=mysql+pymysql://user:pass@host/mydatabase



example setup for mysql on ubuntu

sudo apt install mariadb-server mariadb-client -y
sudo apt install git -y
sudo apt install python3-pip
cd ~/Scaricati
git clone https://github.com/geo-petrini/msg_in_a_flask.git
pip install -r requirements.txt

sudo mysql
CREATE DATABASE `msg_in_a_flask`;
CREATE USER 'msg_user'@'localhost' IDENTIFIED BY 'msg_pass';
GRANT USAGE ON *.* TO 'msg_user'@'localhost';
GRANT ALL  ON `msg_in_a_flask`.* TO 'msg_user'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;

exit

#for cmd

set DB_CONN_STR=mysql+pymysql://msg_user:msg_pass@localhost/msg_in_a_flask

#for ps

$env:DB_CONN_STR='mysql+pymysql://msg_user:msg_pass@localhost/msg_in_a_flask'

#for bash

export DB_CONN_STR=mysql+pymysql://msg_user:msg_pass@localhost/msg_in_a_flask

#run the application

python3 app.py


#dump db for backup

mysqldump -u msg_user --password=msg_pass msg_in_a_flask > `date +"%Y%m%d_%H%M%S"`_msg_in_a_flask.dump

#restore db from backup

mysql msg_in_a_flask < [timestamp]_msg_in_a_flask.dump
