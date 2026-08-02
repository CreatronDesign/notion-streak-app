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

# -----------------------
# TIME HELPERS
# -----------------------

def today_dt():
    return datetime.utcnow() + IST


def today_str():
    return today_dt().strftime("%Y-%m-%d")


# -----------------------
# NOTION DATA
# -----------------------

def get_data():
    """
    Fetch ALL pages from the database.
    Supports pagination (100+ pages).
    """

    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

    results = []
    start_cursor = None

    while True:

        payload = {}

        if start_cursor:
            payload["start_cursor"] = start_cursor

        try:
            res = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=20
            )

            res.raise_for_status()

        except requests.RequestException as e:
            print("Notion API Error:", e)
            return []

        data = res.json()

        if "results" not in data:
            print("Unexpected Notion response:")
            print(data)
            return []

        results.extend(data["results"])

        if not data.get("has_more"):
            break

        start_cursor = data.get("next_cursor")

    return results


def build_days(tasks):

    days = {}

    for i, task in enumerate(tasks):

        props = task.get("properties", {})

        if not props:
            print(f"Skipping page #{i}: no properties")
            continue

        if "Date & Time" not in props:
            print("=" * 80)
            print("BAD PAGE FOUND")
            print("Index:", i)
            print("Page ID:", task.get("id"))
            print("Properties:", list(props.keys()))
            print("=" * 80)
            continue

        if "Today's Work" not in props:
            print("=" * 80)
            print("Missing Today's Work")
            print("Index:", i)
            print("Page ID:", task.get("id"))
            print("=" * 80)
            continue

        date_obj = props["Date & Time"].get("date")

        if not date_obj:
            continue

        d = date_obj["start"][:10]

        done = props["Today's Work"].get("checkbox", False)

        page_id = task["id"].replace("-", "")

        if d not in days:
            days[d] = {
                "checks": [],
                "page_id": page_id
            }

        days[d]["checks"].append(done)


    return days


def success(day):
    return (
        len(day["checks"]) > 0
        and all(day["checks"])
    )

# -----------------------
# STREAK LOGIC
# -----------------------

def calculate_streak(days):

    current = today_dt()

    today = current.strftime("%Y-%m-%d")

    # If today is incomplete,
    # start counting from yesterday.
    if today not in days or not success(days[today]):
        current -= timedelta(days=1)

    streak = 0

    while True:

        ds = current.strftime("%Y-%m-%d")

        if ds in days and success(days[ds]):
            streak += 1
            current -= timedelta(days=1)
        else:
            break

    return streak


# -----------------------
# REALM (HEATMAP)
# -----------------------

def monthly_grid(days):

    now = today_dt()

    year = now.year
    month = now.month

    cal = calendar.Calendar(firstweekday=0)

    grid = []

    today = today_str()

    for dt in cal.itermonthdates(year, month):

        ds = dt.strftime("%Y-%m-%d")

        in_month = dt.month == month

        state = "empty"
        page = ""

        if ds in days:

            if success(days[ds]):
                state = "active"

            else:

                if ds < today:
                    state = "broken"
                else:
                    state = "empty"

            page = (
                f"https://www.notion.so/"
                f"{days[ds]['page_id']}"
            )

        # -------------------------
        # Connected streak logic
        # -------------------------

        left = False
        right = False

        if state == "active":

            prev_day = (
                dt - timedelta(days=1)
            ).strftime("%Y-%m-%d")

            next_day = (
                dt + timedelta(days=1)
            ).strftime("%Y-%m-%d")

            left = (
                prev_day in days
                and success(days[prev_day])
            )

            right = (
                next_day in days
                and success(days[next_day])
            )

        grid.append({
            "date": ds,
            "day": dt.day,
            "in_month": in_month,
            "state": state,
            "url": page,
            "left": left,
            "right": right,
            "today": ds == today
        })

    return grid


def yearly_counts(days):

    now = today_dt()

    year = now.year

    out = []

    for m in range(1, 13):

        count = 0

        for d, v in days.items():

            if (
                d.startswith(f"{year}-{m:02d}")
                and success(v)
            ):
                count += 1

        out.append({
            "month": calendar.month_abbr[m],
            "count": count
        })

    return out

# -----------------------
# ROUTES
# -----------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/data")
def data():

    tasks = get_data()
    days = build_days(tasks)

    today = today_str()

    today_tasks = days.get(today, {"checks": []})["checks"]

    total = len(today_tasks)
    done = sum(today_tasks)
    all_done = total > 0 and all(today_tasks)

    return jsonify({
        "done": done,
        "total": total,
        "all_done": all_done,
        "streak": calculate_streak(days)
    })


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


# -----------------------
# START SERVER
# -----------------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    print("=" * 60)
    print("Notion Streak App")
    print("Database ID:", DATABASE_ID)
    print("Port:", port)
    print("=" * 60)

    app.run(
        host="0.0.0.0",
        port=port
    )
