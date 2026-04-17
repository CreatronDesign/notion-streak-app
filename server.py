from flask import Flask, jsonify, render_template
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
import os

app = Flask(__name__)
CORS(app)


NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def get_today():
    return (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d")

def get_data():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    res = requests.post(url, headers=headers)
    return res.json().get("results", [])

def calculate_streak(tasks):
    days = {}

    for task in tasks:
        props = task["properties"]

        if props["Date & Time"]["date"] is None:
            continue

        date = props["Date & Time"]["date"]["start"][:10]
        done = props["Today's Work"]["checkbox"]

        days.setdefault(date, []).append(done)

    today = get_today()

    if today in days:
        if all(days[today]):
            start_date = datetime.strptime(today, "%Y-%m-%d")
        else:
            start_date = datetime.strptime(today, "%Y-%m-%d") - timedelta(days=1)
    else:
        if not days:
            return 0
        latest_day = max(days.keys())
        start_date = datetime.strptime(latest_day, "%Y-%m-%d")

    streak = 0
    current = start_date

    while True:
        d = current.strftime("%Y-%m-%d")

        if d in days and all(days[d]):
            streak += 1
            current -= timedelta(days=1)
        else:
            break

    return streak

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/data")
def data():
    tasks = get_data()
    today = get_today()

    today_tasks = []

    for t in tasks:
        props = t["properties"]

        if props["Date & Time"]["date"] is None:
            continue

        date = props["Date & Time"]["date"]["start"][:10]

        if date == today:
            today_tasks.append(props["Today's Work"]["checkbox"])

    total = len(today_tasks)
    done = sum(today_tasks)
    all_done = total > 0 and all(today_tasks)

    return jsonify({
        "done": done,
        "total": total,
        "all_done": all_done,
        "streak": calculate_streak(tasks)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))