from flask import Flask, jsonify, render_template
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
import calendar
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

IST = timedelta(hours=5, minutes=30)

def today_dt():
    return datetime.utcnow() + IST

def today_str():
    return today_dt().strftime("%Y-%m-%d")

def get_data():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    res = requests.post(url, headers=headers)
    return res.json().get("results", [])

def build_days(tasks):
    days = {}

    for task in tasks:
        props = task["properties"]
        date_obj = props["Date & Time"]["date"]
        if not date_obj:
            continue

        d = date_obj["start"][:10]
        done = props["Today's Work"]["checkbox"]
        page_id = task["id"].replace("-", "")

        if d not in days:
            days[d] = {"checks": [], "page_id": page_id}

        days[d]["checks"].append(done)

    return days

def success(day):
    return len(day["checks"]) > 0 and all(day["checks"])

def monthly_grid(days):
    now = today_dt()
    year = now.year
    month = now.month

    cal = calendar.Calendar(firstweekday=0)
    grid = []

    for dt in cal.itermonthdates(year, month):
        ds = dt.strftime("%Y-%m-%d")
        in_month = dt.month == month

        state = "empty"
        page = ""

        if ds in days:
            state = "active" if success(days[ds]) else "broken"
            page = f"https://www.notion.so/{days[ds]['page_id']}"

        grid.append({
            "date": ds,
            "day": dt.day,
            "in_month": in_month,
            "state": state,
            "url": page
        })

    return grid

def yearly_counts(days):
    now = today_dt()
    year = now.year
    out = []

    for m in range(1,13):
        count = 0
        for d,v in days.items():
            if d.startswith(f'{year}-{m:02d}') and success(v):
                count += 1
        out.append({"month": calendar.month_abbr[m], "count": count})

    return out

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/realm")
def realm():
    return render_template("realm.html")

@app.route("/realm-data")
def realm_data():
    tasks = get_data()
    days = build_days(tasks)

    return jsonify({
        "month": today_dt().strftime("%B %Y"),
        "grid": monthly_grid(days),
        "year": yearly_counts(days)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))