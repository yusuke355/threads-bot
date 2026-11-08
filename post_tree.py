"""テキストのツリー投稿を Threads に投稿する（年収ノート用）。
   1投稿目を出したあと、2投稿目以降を「自分の投稿への返信」として順につなげる。
   環境変数:
     THREADS_ACCESS_TOKEN … そのアカウントのトークン
     ACCOUNT_DIR          … posts.json / posted.json を置くフォルダ（例: nenshu）
     MODE                 … due=予定時刻を過ぎた分 / next=次の1件を今すぐ
"""
import json, os, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime
from zoneinfo import ZoneInfo

API = "https://graph.threads.net/v1.0"
TOKEN = os.environ["THREADS_ACCESS_TOKEN"]
DIR = os.environ.get("ACCOUNT_DIR", "nenshu")
JST = ZoneInfo("Asia/Tokyo")
MAX_LEN = 500

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
        time.sleep(3)
    raise RuntimeError(f"container {cid} timeout")

def publish_text(text, reply_to=None, topic=None):
    params = dict(media_type="TEXT", text=text)
    if reply_to:
        params["reply_to_id"] = reply_to
    if topic:
        try:
            c = call("POST", "me/threads", topic_tag=topic, **params)
        except RuntimeError as e:
            print("topic_tag なしで再試行:", e)
            c = call("POST", "me/threads", **params)
    else:
        c = call("POST", "me/threads", **params)
    wait_ready(c["id"])
    return call("POST", "me/threads_publish", creation_id=c["id"])["id"]

def path(name):
    return os.path.join(DIR, name)

def save(state):
    json.dump(state, open(path("posted.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def main():
    posts = json.load(open(path("posts.json"), encoding="utf-8"))
    state = json.load(open(path("posted.json"), encoding="utf-8")) if os.path.exists(path("posted.json")) else {}
    for p in posts:  # 文字数チェック（投稿前に気づけるように）
        for i, t in enumerate(p["posts"], 1):
            if len(t) > MAX_LEN:
                raise SystemExit(f"{p['id']} の{i}投稿目が{len(t)}文字です（上限{MAX_LEN}）")
    now = datetime.now(JST)
    mode = os.environ.get("MODE", "due")
    todo = [p for p in posts if not state.get(p["id"], {}).get("done")]
    if mode != "next":
        todo = [p for p in todo if datetime.fromisoformat(p["at"]).replace(tzinfo=JST) <= now]
    for p in todo[:1]:  # 1回の実行で1ツリーまで
        s = state.setdefault(p["id"], {"ids": [], "done": False})
        # 途中で止まった場合は、続きから投稿する（1投稿目の二重投稿を防ぐ）
        for i in range(len(s["ids"]), len(p["posts"])):
            prev = s["ids"][-1] if s["ids"] else None
            mid = publish_text(p["posts"][i], reply_to=prev, topic=None if prev else p.get("topic", "転職"))
            s["ids"].append(mid)
            s["media_id"] = s["ids"][0]
            save(state)
            print("posted", p["id"], i + 1, mid)
            time.sleep(5)
        s["done"] = True
        s["posted_at"] = now.isoformat(timespec="minutes")
        save(state)
        return
    print("nothing to post")

if __name__ == "__main__":
    main()
