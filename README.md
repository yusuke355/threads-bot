# threads-bot

『辞めたい夜に読む言葉』の自動投稿。

- posts.json … 投稿の予定（日時は日本時間）
- images/ … 投稿の画像（build.py で作成）
- posted.json … 投稿済みの記録（自動で更新）
- data/insights.csv … 毎日の数字（自動で更新）

## 年収ノート（nenshu_note35）
- nenshu/posts.json … ツリー投稿の予定（posts に1投稿目から順に本文）
- nenshu/posted.json … 投稿済みの記録（自動で更新）
- nenshu/data/insights.csv … 毎日の数字（自動で更新）
- post_tree.py / insights_tree.py … ツリー投稿と数字の記録
- トークンは Secrets の THREADS_ACCESS_TOKEN_NENSHU
