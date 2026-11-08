"""年収ノートの投稿の数字を <ACCOUNT_DIR>/data/insights.csv に記録する（毎日1回）。
   1投稿目の数字に加え、ツリー全体の返信先までの閲覧数（views_last）も記録する。"""
import csv, json, os
from datetime import datetime
from zoneinfo import ZoneInfo
from post_tree import call, DIR

JST = ZoneInfo("Asia/Tokyo")
METRICS = "views,likes,replies,reposts,quotes,shares"

def get(mid):
    r = call("GET", f"{mid}/insights", metric=METRICS)
    return {d["name"]: d["values"][0]["value"] if "values" in d else d.get("total_value", {}).get("value") for d in r["data"]}

state = json.load(open(os.path.join(DIR, "posted.json"), encoding="utf-8")) if os.path.exists(os.path.join(DIR, "posted.json")) else {}
os.makedirs(os.path.join(DIR, "data"), exist_ok=True)
out = os.path.join(DIR, "data", "insights.csv")
new = not os.path.exists(out)
today = datetime.now(JST).strftime("%Y-%m-%d")
with open(out, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    if new:
        w.writerow(["date", "post_id", "views", "likes", "replies", "reposts", "quotes", "shares", "views_last"])
    for pid, v in state.items():
        if not v.get("ids"):
            continue
        try:
            m = get(v["ids"][0])
            last = get(v["ids"][-1]).get("views") if len(v["ids"]) > 1 else ""
            w.writerow([today, pid, m.get("views"), m.get("likes"), m.get("replies"), m.get("reposts"), m.get("quotes"), m.get("shares"), last])
        except Exception as e:
            print("skip", pid, e)
print("insights saved")
