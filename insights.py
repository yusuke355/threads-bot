"""投稿済みの各投稿の数字を data/insights.csv に記録する（毎日1回）"""
import csv, json, os
from datetime import datetime
from zoneinfo import ZoneInfo
from post import call
JST = ZoneInfo("Asia/Tokyo")
state = json.load(open("posted.json", encoding="utf-8")) if os.path.exists("posted.json") else {}
os.makedirs("data", exist_ok=True)
path = "data/insights.csv"
new = not os.path.exists(path)
today = datetime.now(JST).strftime("%Y-%m-%d")
with open(path, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    if new:
        w.writerow(["date", "post_id", "views", "likes", "replies", "reposts", "quotes", "shares"])
    for pid, v in state.items():
        try:
            r = call("GET", f"{v['media_id']}/insights", metric="views,likes,replies,reposts,quotes,shares")
            m = {d["name"]: d["values"][0]["value"] if "values" in d else d.get("total_value", {}).get("value") for d in r["data"]}
            w.writerow([today, pid, m.get("views"), m.get("likes"), m.get("replies"), m.get("reposts"), m.get("quotes"), m.get("shares")])
        except Exception as e:
            print("skip", pid, e)
print("insights saved")
