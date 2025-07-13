from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allow frontend to call the API

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['github_events']
collection = db['events']

#Serving the frontend
@app.route('/')
def home():
    return render_template('index.html')

#calling the webhook to fetch data
@app.route('/github', methods=['POST'])
def github_webhook():
    if request.is_json:
        payload = request.get_json()
        event_type = request.headers.get('X-GitHub-Event', '').upper()
        author = None
        request_id = None
        from_branch = None
        to_branch = None
        timestamp = datetime.utcnow().strftime('%d %B %Y - %I:%M %p UTC')
        action = event_type

        if event_type == 'PUSH':
            author = payload.get('pusher', {}).get('name')
            request_id = payload.get('head_commit', {}).get('id')
            to_branch = payload.get('ref', '').split('/')[-1]

        elif event_type == 'PULL_REQUEST':
            pr = payload.get('pull_request', {})
            author = pr.get('user', {}).get('login')
            request_id = pr.get('id')
            from_branch = pr.get('head', {}).get('ref')
            to_branch = pr.get('base', {}).get('ref')
            timestamp = pr.get('updated_at', timestamp)
            if payload.get('action') == 'closed' and pr.get('merged'):
                action = "MERGE"

        else:
            return jsonify({"message": "Unhandled event type"}), 400

        document = {
            "request_id": str(request_id),
            "author": author,
            "action": action,
            "from_branch": from_branch,
            "to_branch": to_branch,
            "timestamp": timestamp
        }

        #inserting data into the database
        collection.insert_one(document)
        return jsonify({"message": "Data saved"}), 200

    return jsonify({"error": "Invalid JSON"}), 400

@app.route('/events', methods=['GET'])
def get_events():
    data = list(collection.find({}, {"_id": 0}))
    return jsonify(data), 200

if __name__ == '__main__':
    app.run(debug=True)
