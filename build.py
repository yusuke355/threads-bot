"""posts.json の各投稿の画像を images/<id>/<n>.png に作る"""
import json, os
from render import render
posts = json.load(open("posts.json", encoding="utf-8"))
for p in posts:
    d = os.path.join("images", p["id"])
    os.makedirs(d, exist_ok=True)
    for i, cols in enumerate(p["slides"], 1):
        path = os.path.join(d, f"{i}.jpg")
        if not os.path.exists(path):
            render(cols, path, seed=hash(p["id"]) % 1000 + i)
print("built", len(posts))
