# msg_in_a_flask

## Info
Small flask chat demo using `gunicorn` and `flask_socketio`.
In addition to simple chat with users the site "sings". If someone sends the `//sing` string the application will broadcast song lyrics.


Deploy with an environment variables `DB_CONN_STR` and `SECRET_KEY`

### Examples
```python
# PostgreSQL
DB_CONN_STR=postgresql+psycopg2://user:pass@host:5432/mydatabase

# MysSQL
DB_CONN_STR=mysql+pymysql://user:pass@host/mydatabase

# Sqlite
DB_CONN_STR=sqlite:///mydatabase.db

SECRET_KEY='very strong secret key with numbers 0123 and special chars !'

```

### Setup of env variables from command line

**Windows cmd**
```cmd
set DB_CONN_STR=mysql+pymysql://msg_user:msg_pass@localhost/msg_in_a_flask
```
**Windows PowerShell**
```ps
$env:DB_CONN_STR='mysql+pymysql://msg_user:msg_pass@localhost/msg_in_a_flask'
```
**Bash**
```bash
export DB_CONN_STR=mysql+pymysql://msg_user:msg_pass@localhost/msg_in_a_flask
```

### Env file
The application supports `.env` files for convencience.


## Setup example for mysql on ubuntu
```shell
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
```


## Run the application

`python3 app.py`


## Dump db for backup

```shell
mysqldump -u msg_user --password=msg_pass msg_in_a_flask > `date +"%Y%m%d_%H%M%S"`_msg_in_a_flask.dump
```
## Restore db from backup

```shell
mysql msg_in_a_flask < [timestamp]_msg_in_a_flask.dump
```


## Future additions
- Load songs from a website with lyrics such as https://www.lyrics.com
- Use an LLM for generating new songs based on user prompts