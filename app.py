あなたはシニアPythonエンジニア兼UIデザイナーです。

以下の仕様を満たす、保守性・可読性・拡張性の高いStreamlitアプリを作成してください。

# アプリ名
RoboHub

# 使用技術
- Python 3.12
- Streamlit
- Supabase(supabase-py)
- pandas

# ディレクトリ構成

app.py
database.py
utils.py
requirements.txt

# 認証
SupabaseのURL・KEYはst.secretsから取得すること。

# データベース

テーブル名
tasks

カラム

task_name text
team text
assignee text
status text
progress int
deadline date
attachment_url text
updated_at timestamp

# 機能

・タスク追加フォーム
・task_name必須
・attachment_url必須
・期限入力
・担当者入力
・チーム入力
・進捗0〜100
・ステータス
    未着手
    進行中
    完了

・一覧表示
st.data_editorを使用

編集可能項目
・task_name
・team
・assignee
・status
・progress
・deadline
・attachment_url

編集後は「保存」ボタンでSupabaseへ更新

削除チェックボックスを付ける

期限切れは赤文字表示

# 検索

サイドバーに

・担当者検索
・チーム検索
・ステータス検索

# ダッシュボード

上部に

総タスク数

進行中

完了

期限切れ

をst.metricで表示

# エラー処理

try-exceptを使用し

接続失敗

保存失敗

更新失敗

削除失敗

はst.errorで表示

# コード品質

PEP8準拠

型ヒント

Docstring

関数分割

コメント付き

# 出力

以下を順番に出力

1.app.py

2.database.py

3.utils.py

4.requirements.txt

コードはそのまま実行できる完成形にしてください。
