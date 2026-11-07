"""予定時刻を過ぎた未投稿の投稿を、Threadsにカルーセルで投稿する。
   MODE=next のときは、時刻に関係なく次の未投稿を1件だけ投稿する（テスト用）。"""
import json, os, sys, time, urllib.parse, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

API = "https://graph.threads.net/v1.0"
TOKEN = os.environ["THREADS_ACCESS_TOKEN"]
REPO = os.environ.get("GITHUB_REPOSITORY", "yusuke355/threads-bot")
RAW = f"https://raw.githubusercontent.com/{REPO}/main/images"
JST = ZoneInfo("Asia/Tokyo")

def call(method, path, **params):
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        req = urllib.request.Request(url + "?" + data.decode())
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{path}: {e.code} {e.read().decode()[:500]}")

def wait_ready(cid):
    for _ in range(30):
        st = call("GET", cid, fields="status,error_message")
        if st.get("status") == "FINISHED":
            return
        if st.get("status") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container {cid}: {st}")
        time.sleep(5)
    raise RuntimeError(f"container {cid} timeout")

def publish(p):
    children = []
    for i in range(1, len(p["slides"]) + 1):
        c = call("POST", "me/threads", media_type="IMAGE", is_carousel_item="true",
                 image_url=f"{RAW}/{p['id']}/{i}.jpg")
        children.append(c["id"])
    for c in children:
        wait_ready(c)
    car = call("POST", "me/threads", media_type="CAROUSEL",
               children=",".join(children), text=p["caption"])
    wait_ready(car["id"])
    res = call("POST", "me/threads_publish", creation_id=car["id"])
    return res["id"]

def main():
    posts = json.load(open("posts.json", encoding="utf-8"))
    state = json.load(open("posted.json", encoding="utf-8")) if os.path.exists("posted.json") else {}
    now = datetime.now(JST)
    mode = os.environ.get("MODE", "due")
    todo = [p for p in posts if p["id"] not in state]
    if mode != "next":
        todo = [p for p in todo if datetime.fromisoformat(p["at"]).replace(tzinfo=JST) <= now]
    todo = todo[:1]   # 1回の実行で投稿するのは1件まで（連投防止）
    for p in todo:
        mid = publish(p)
        state[p["id"]] = {"media_id": mid, "posted_at": now.isoformat(timespec="minutes")}
        print("posted", p["id"], mid)
    json.dump(state, open("posted.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if not todo:
        print("nothing to post")

if __name__ == "__main__":
    main()
