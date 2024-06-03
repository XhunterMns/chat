import random
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

messages = []
users = []
pairs = {}

@app.route('/')
def choose_username():
    return render_template('index.html')

@app.route('/set_username', methods=['POST'])
def set_username():
    username = request.form['name']
    session['username'] = username
    users.append(username)
    session['paired'] = False
    return redirect(url_for('chatroom'))

@app.route('/chatroom')
def chatroom():
    if 'username' not in session:
        return redirect(url_for('choose_username'))
    pair_user()
    return render_template('chat_room.html', messages=messages, username=session['username'], paired=session['paired'])

@app.route('/logout', methods=['POST'])
def logout():
    username = session.get('username')
    if username in users:
        users.remove(username)
    if username in pairs:
        partner = pairs.pop(username, None)
        if partner:
            pairs.pop(partner, None)
    session.pop('username', None)
    return redirect(url_for('choose_username'))

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'username' not in session:
        return redirect(url_for('choose_username'))

    name = session['username']
    message_text = request.form['message']
    timestamp = datetime.now()
    file = request.files.get('file')
    file_path = None

    if file:
        filename = f"{timestamp.strftime('%Y%m%d%H%M%S')}_{file.filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        file_path = os.path.join('uploads', filename)

    new_message = {'name': name, 'message': message_text, 'timestamp': timestamp, 'file_path': file_path}
    messages.append(new_message)
    return redirect(url_for('chatroom'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/check_pairing')
def check_pairing():
    username = session.get('username')
    paired = session.get('paired', False)
    return jsonify({'paired': paired})

@app.route('/skip', methods=['POST'])
def skip():
    username = session.get('username')
    if username in pairs:
        partner = pairs.pop(username, None)
        if partner:
            pairs.pop(partner, None)
            clear_messages(username, partner)
    session['paired'] = False
    pair_user()  # Pair the skipping user with another random user
    return redirect(url_for('chatroom'))

def pair_user():
    global pairs
    if len(users) >= 2:
        available_users = [user for user in users if user not in pairs]
        if len(available_users) >= 2:
            user1 = random.choice(available_users)
            available_users.remove(user1)
            user2 = random.choice(available_users)
            pairs[user1] = user2
            pairs[user2] = user1
            session['paired'] = True

def clear_messages(user1, user2):
    global messages
    messages = [m for m in messages if m['name'] not in (user1, user2)]

if __name__ == '__main__':
    app.run(debug=True)
