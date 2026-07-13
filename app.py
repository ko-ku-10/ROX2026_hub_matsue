import streamlit as st
import pandas as pd
from supabase import create_client, Client
import time
from datetime import date

# ページ設定
st.set_page_config(
    page_title="RoboHub - ロボコンプロジェクト管理",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 1. Supabaseの初期化 ---
# セキュリティ要件に基づき st.secrets から読み込み
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("Supabaseの認証情報が見つかりません。.streamlit/secrets.toml を設定してください。")
    st.stop()


# --- 2. データベース操作用ヘルパー関数 ---

def fetch_tasks() -> pd.DataFrame:
    """Supabaseから全タスクを取得してPandas DataFrameに変換する関数"""
    try:
        response = supabase.table("tasks").select("*").order("created_at", desc=True).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            
            # データベースの英語カラム名をアプリ内の日本語表示名にマッピング
            column_mapping = {
                "task_name": "タスク名",
                "team": "担当班",
                "assignee": "担当者",
                "status": "ステータス",
                "progress": "進捗度",
                "due_date": "予定日",
                "completed_date": "完了日",
                "related_link": "関連リンク"
            }
            df = df.rename(columns=column_mapping)
            
            # 日付カラムの型調整
            if "予定日" in df.columns:
                df["予定日"] = pd.to_datetime(df["予定日"]).dt.date
            if "完了日" in df.columns:
                df["完了日"] = pd.to_datetime(df["完了日"]).dt.date.fillna(pd.NaT)
                
            return df
        else:
            # データが空の場合のデフォルト構造
            return pd.DataFrame(columns=["タスク名", "担当班", "担当者", "ステータス", "進捗度", "予定日", "完了日", "関連リンク"])
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return pd.DataFrame()

def upload_file_to_storage(uploaded_file) -> str:
    """ファイルをSupabase Storageにアップロードし、公開URLを返す関数"""
    if uploaded_file is not None:
        try:
            file_bytes = uploaded_file.read()
            # ファイル名の重複を防ぐためタイムスタンプを付与
            file_name = f"{int(time.time())}_{uploaded_file.name}"
            
            # attachmentsバケットへアップロード
            supabase.storage.from_("attachments").upload(
                path=file_name,
                file=file_bytes,
                file_options={"content-type": uploaded_file.type}
            )
            
            # 公開URLの取得
            public_url = supabase.storage.from_("attachments").get_public_url(file_name)
            return public_url
        except Exception as e:
            st.error(f"ファイルアップロードエラー: {e}")
            return None
    return None

def insert_task(task_data: dict):
    """Supabaseのtasksテーブルにデータをインサートする関数"""
    try:
        supabase.table("tasks").insert(task_data).execute()
        st.success("タスクが正常に保存されました！")
        time.sleep(1) # 成功メッセージを見せるための待機
        st.rerun()    # 画面を更新して最新データを反映
    except Exception as e:
        st.error(f"タスク保存エラー: {e}")


# --- 3. UI構築 ---
st.title("🤖 RoboHub - チームプロジェクト管理 (Supabase連携版)")
st.markdown("ロボコンチームのタスク・スケジュール・活動履歴をSupabaseで一元管理するダッシュボードです。")

# 最新データの取得
df = fetch_tasks()

# 3つのタブを作成
tab1, tab2, tab3 = st.tabs(["📌 現在のタスク", "📅 これからの予定", "📖 活動ログ（今までやったこと）"])

# 各フォームで共通して利用する選択肢
TEAMS = ["メカ", "電装", "制御", "事務"]


# --- タブ1：現在のタスク ---
with tab1:
    st.header("進行中のタスク一覧")
    
    # 新規タスク追加フォーム
    with st.expander("➕ 新規タスクの追加 / 資料のアップロード", expanded=False):
        with st.form(key="form_current"):
            col1, col2 = st.columns(2)
            with col1:
                t_name = st.text_input("タスク名", key="c_name")
                t_team = st.selectbox("担当班", TEAMS, key="c_team")
                t_assignee = st.text_input("担当者", key="c_assignee")
            with col2:
                t_due = st.date_input("予定日", value=date.today(), key="c_due")
                t_progress = st.slider("初期進捗度", 0, 100, 30, key="c_progress") # 進行中なので初期30%など
                t_file = st.file_uploader("関連資料・設計図などのアップロード", key="c_file")
            
            submitted1 = st.form_submit_button("タスクを追加して保存")
            if submitted1:
                if not t_name:
                    st.warning("タスク名を入力してください。")
                else:
                    # ファイルがあればストレージにアップロードしてURLを取得
                    file_url = upload_file_to_storage(t_file)
                    
                    # インサート用データの組み立て (カラム名はデータベースに合わせる)
                    new_task = {
                        "task_name": t_name,
                        "team": t_team,
                        "assignee": t_assignee,
                        "status": "進行中",
                        "progress": t_progress,
                        "due_date": str(t_due),
                        "related_link": file_url if file_url else None
                    }
                    insert_task(new_task)

    st.divider()

    # 進行中のタスクを表示
    if not df.empty and "ステータス" in df.columns:
        df_current = df[df["ステータス"] == "進行中"].reset_index(drop=True)
    else:
        df_current = pd.DataFrame()
    
    if df_current.empty:
        st.info("現在進行中のタスクはありません。")
    else:
        for index, row in df_current.iterrows():
            with st.container():
                col_info, col_prog = st.columns([1, 2])
                with col_info:
                    st.subheader(row["タスク名"])
                    st.caption(f"担当: {row['担当班']}班 ({row['担当者']}) | 期限: {row['予定日']}")
                    if row["関連リンク"]:
                        st.markdown(f"[🔗 関連資料リンク]({row['関連リンク']})")
                
                with col_prog:
                    st.write(f"進捗度: {row['進捗度']}%")
                    st.progress(int(row["進捗度"]))
                st.write("---")


# --- タブ2：これからの予定 ---
with tab2:
    st.header("今後のスケジュール")
    
    # 予定追加フォーム
    with st.expander("📅 予定の追加 / 仕様書のアップロード", expanded=False):
        with st.form(key="form_future"):
            col1, col2 = st.columns(2)
            with col1:
                f_name = st.text_input("予定タスク名")
                f_team = st.selectbox("担当班", TEAMS)
                f_assignee = st.text_input("担当者")
            with col2:
                f_due = st.date_input("開始予定日", value=date.today() + pd.Timedelta(days=7))
                f_file = st.file_uploader("参考資料のアップロード")
                
            submitted2 = st.form_submit_button("予定を追加して保存")
            if submitted2:
                if not f_name:
                    st.warning("予定タスク名を入力してください。")
                else:
                    file_url = upload_file_to_storage(f_file)
                    new_future_task = {
                        "task_name": f_name,
                        "team": f_team,
                        "assignee": f_assignee,
                        "status": "未着手",
                        "progress": 0,
                        "due_date": str(f_due),
                        "related_link": file_url if file_url else None
                    }
                    insert_task(new_future_task)

    st.divider()

    # 未着手のタスクを表示
    if not df.empty and "ステータス" in df.columns:
        df_future = df[df["ステータス"] == "未着手"].sort_values(by="予定日").reset_index(drop=True)
    else:
        df_future = pd.DataFrame()
    
    if df_future.empty:
        st.info("これからの予定は登録されていません。")
    else:
        st.dataframe(
            df_future[["予定日", "タスク名", "担当班", "担当者", "関連リンク"]],
            use_container_width=True,
            hide_index=True
        )


# --- タブ3：活動ログ（今までやったこと） ---
with tab3:
    st.header("完了済みタスク・活動ログ")
    
    # 活動記録フォーム
    with st.expander("📝 議事録・活動記録のアップロード", expanded=False):
        with st.form(key="form_log"):
            col1, col2 = st.columns(2)
            with col1:
                l_name = st.text_input("記録タイトル（完了タスク名）")
                l_team = st.selectbox("担当班", TEAMS)
                l_assignee = st.text_input("担当者")
            with col2:
                l_done_date = st.date_input("完了日", value=date.today())
                l_file = st.file_uploader("完了報告書・テスト動画のアップロード")
                
            submitted3 = st.form_submit_button("記録を保存")
            if submitted3:
                if not l_name:
                    st.warning("タイトルを入力してください。")
                else:
                    file_url = upload_file_to_storage(l_file)
                    new_done_task = {
                        "task_name": l_name,
                        "team": l_team,
                        "assignee": l_assignee,
                        "status": "完了",
                        "progress": 100,
                        "completed_date": str(l_done_date),
                        "related_link": file_url if file_url else None
                    }
                    insert_task(new_done_task)

    st.divider()

    # 完了済みのタスクを表示
    if not df.empty and "ステータス" in df.columns:
        df_done = df[df["ステータス"] == "完了"].sort_values(by="完了日", ascending=False).reset_index(drop=True)
    else:
        df_done = pd.DataFrame()
    
    if df_done.empty:
        st.info("完了済みのタスクはまだありません。")
    else:
        for index, row in df_done.iterrows():
            with st.container():
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.metric(label="完了日", value=str(row["完了日"]))
                with col2:
                    st.success(f"✅ **{row['タスク名']}**")
                    st.write(f"担当: {row['担当班']}班 - {row['担当者']}")
                    if row["関連リンク"]:
                        st.markdown(f"[🔗 添付ファイル・報告書を開く]({row['関連リンク']})")
                st.write("---")