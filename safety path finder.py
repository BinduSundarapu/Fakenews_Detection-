from flask import Flask, render_template, request, redirect, session, url_for
import pandas as pd
import json
from collections import deque
app = Flask(__name__)
app.secret_key = 'your_secret_key'
def load_graph():
    with open("all_pincode_paths.json") as f:
        raw_list = json.load(f)

    graph = {}
    for entry in raw_list:
        for key, value in entry.items():
            if key not in graph:
                graph[key] = []
            graph[key].extend(value)

    # Optional: remove duplicate neighbors
    return {k: list(set(v)) for k, v in graph.items()}

# ✅ Load the safety scores
def load_safety_scores():
    df = pd.read_csv("safety_data_updated.csv")
    scores = {}
    for _, row in df.iterrows():
        area = str(int(row['area']))
        outcome = float(row['outcome']) if 'outcome' in row else float(row['class'])
        if area not in scores:
            scores[area] = []
        scores[area].append(outcome)
    return {k: sum(v)/len(v) for k, v in scores.items()}

# ✅ Find all possible paths using BFS
def find_all_paths(graph, start, end, max_depth=6):
    queue = deque([[start]])
    paths = []

    while queue:
        path = queue.popleft()
        node = path[-1]

        if node == end:
            paths.append(path)
            continue

        if len(path) > max_depth:
            continue

        for neighbor in graph.get(node, []):
            if neighbor not in path:
                queue.append(path + [neighbor])
    return paths
# ✅ Hardcoded users for demo
users = {
    "admin": {"password": "admin123"},
    "testuser": {"password": "testpass"}
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])  # must allow POST
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            session['username'] = username
            return redirect('/about')
        else:
            return render_template('index.html', error='Invalid credentials')
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')  # Disabled registration for now

@app.route('/about')
def about():
    if 'username' not in session:
        return redirect('/')
    return render_template('about.html')

@app.route('/find')
def find():
    if 'username' not in session:
        return redirect('/')
    return render_template('pathfinder.html')

@app.route('/find_path', methods=['POST'])
def find_path():
    if 'username' not in session:
        return redirect('/')

    source = request.form['source']
    destination = request.form['destination']

    graph = load_graph()
    safety_scores = load_safety_scores()

    paths = find_all_paths(graph, source, destination)

    if not paths:
        return render_template('pathfinder.html', result="No safe paths found.")

    result_routes = []
    for path in paths:
        scores = [safety_scores.get(str(pin), 150) for pin in path]  # default score if missing
        avg = round(sum(scores) / len(scores), 3)

        if avg < 150:
            code = "🟢 Safe"
        elif avg < 160:
            code = "🟡 Moderate"
        else:
            code = "🔴 Risky"

        result_routes.append({
            "path": path,
            "mean_safety": avg,
            "safety_code": code
        })

    best = min(result_routes, key=lambda x: x['mean_safety'])

    return render_template('pathfinder.html', result={"best": best, "routes": result_routes})

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if 'username' not in session:
        return redirect('/')
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        print(f'Message from {name} <{email}>: {message}')
        return redirect('/contact')
    return render_template('contact.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
