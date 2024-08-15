from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from bson import ObjectId
import os

app = Flask(__name__)

mongo_uri = os.getenv('MONGO_URI', 'mongodb://mongo:1111/taskdb')
client = MongoClient(mongo_uri)
db = client.taskdb

def validate_user_data(data):
    required_fields = {'name', 'username', 'interval'}
    if not all(field in data for field in required_fields):
        return False
    if not isinstance(data['interval'], int) or data['interval'] <= 0:
        return False
    if db.users.find_one({'username': data['username']}):
        return False
    return True

def validate_task_data(data):
    required_fields = {'username', 'description', 'deadline'}
    if not all(field in data for field in required_fields):
        return False
    try:
        datetime.strptime(data['deadline'], '%Y-%m-%d')
    except ValueError:
        return False
    return True

@app.route('/', methods=['GET'])
def ping_server():
    return "Server is running"

@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.json
    if not validate_user_data(data):
        return jsonify({'message': 'Invalid data'}), 400
    user = {
        'name': data['name'],
        'username': data['username'],
        'interval': data['interval']
    }
    db.users.insert_one(user)
    return jsonify({'message': 'User added successfully'}), 201

@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.json
    if not validate_task_data(data):
        return jsonify({'message': 'Invalid data'}), 400
    task = {
        'username': data['username'],
        'description': data['description'],
        'deadline': datetime.strptime(data['deadline'], '%Y-%m-%d'),
        'completed': False
    }
    db.tasks.insert_one(task)
    return jsonify({'message': 'Task added successfully'}), 201

@app.route('/get_tasks/<username>', methods=['GET'])
def get_tasks(username):
    tasks = list(db.tasks.find({'username': username, 'completed': False}, {'_id': 1, 'description': 1, 'deadline': 1}))
    for task in tasks:
        task['_id'] = str(task['_id'])
    return jsonify(tasks)

@app.route('/complete_task', methods=['POST'])
def complete_task():
    data = request.json
    db.tasks.update_one({'_id': ObjectId(data['task_id'])}, {'$set': {'completed': True}})
    return jsonify({'message': 'Task marked as completed'}), 200

@app.route('/get_overdue_tasks/<username>', methods=['GET'])
def get_overdue_tasks(username):
    overdue_tasks = list(db.tasks.find({'username': username, 'deadline': {'$lt': datetime.now()}, 'completed': False}, {'_id': 1, 'description': 1, 'deadline': 1}))
    for task in overdue_tasks:
        task['_id'] = str(task['_id'])
    return jsonify(overdue_tasks)

@app.route('/delete_overdue_reports', methods=['POST'])
def delete_overdue_reports():
    data = request.json
    db.tasks.update_many({'username': data['username'], 'completed': False, 'deadline': {'$lt': datetime.now()}}, {'$set': {'completed': True}})
    return jsonify({'message': 'Overdue reports cleared'}), 200

def send_reminder(username):
    tasks = list(db.tasks.find({'username': username, 'completed': False}))
    if tasks:
        print(f"Reminder for {username}:")
        for task in tasks:
            print(f"Task: {task['description']}, Deadline: {task['deadline']}")

def schedule_reminders():
    scheduler = BackgroundScheduler()
    users = list(db.users.find())
    for user in users:
        scheduler.add_job(send_reminder, 'interval', days=user['interval'], args=[user['username']], id=f"reminder_{user['username']}")
    scheduler.start()

if __name__ == "__main__":
    schedule_reminders()
    app.run(host='0.0.0.0', port=5000, debug=True)
