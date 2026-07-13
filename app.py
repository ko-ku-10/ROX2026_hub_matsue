from datetime import date
import pandas as pd
import streamlit as st
from supabase import create_client, Client

# -----------------------------
# Streamlit Config
# -----------------------------
st.set_page_config(
    page_title="RoboHub",
    page_icon="🤖",
    layout="wide"
)

STATUS_OPTIONS = ["未着手", "進行中", "完了"]


# -----------------------------
# Supabase
# -----------------------------
@st.cache_resource
def init_supabase() -> Client:
    """Supabaseクライアント生成"""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Supabase設定を読み込めません。\n\n{e}")
        st.stop()


supabase = init_supabase()


# -----------------------------
# Database
# -----------------------------
def load_tasks():
    """タスク取得"""
    try:
        response = (
            supabase.table("tasks")
            .select("*")
            .order("updated_at", desc=True)
            .execute()
        )

        if response.data:
            return pd.DataFrame(response.data)

        return pd.DataFrame(columns=[
            "id",
            "task_name",
            "team",
            "assignee",
            "status",
            "progress",
            "deadline",
            "attachment_url",
            "updated_at"
        ])

    except Exception as e:
        st.error(f"タスク取得に失敗しました。\n\n{e}")
        return pd.DataFrame()


def add_task(data: dict):
    """タスク追加"""
    try:
        supabase.table("tasks").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"保存に失敗しました。\n\n{e}")
        return False


def update_task(row: dict):
    """タスク更新"""

    task_id = row["id"]

    payload = {
        "task_name": row["task_name"],
        "team": row["team"],
        "assignee": row["assignee"],
        "status": row["status"],
        "progress": int(row["progress"]),
        "deadline": str(row["deadline"]),
        "attachment_url": row["attachment_url"],
    }

    try:
        (
            supabase.table("tasks")
            .update(payload)
            .eq("id", task_id)
            .execute()
        )
        return True

    except Exception as e:
        st.error(f"更新エラー\n\n{e}")
        return False


# -----------------------------
# Header
# -----------------------------
st.title("🤖 RoboHub")
st.caption("Supabase × Streamlit Project Manager")

# -----------------------------
# Add Task
# -----------------------------
st.header("タスク追加")

with st.form("task_form", clear_on_submit=True):

    col1, col2 = st.columns(2)

    with col1:
        task_name = st.text_input("タスク名")
        team = st.text_input("チーム")
        assignee = st.text_input("担当者")
        deadline = st.date_input("期限", value=date.today())

    with col2:
        status = st.selectbox("ステータス", STATUS_OPTIONS)
        progress = st.slider("進捗", 0, 100, 0)

        attachment = st.text_input(
            "添付資料URL（必須）",
            placeholder="https://..."
        )

    submit = st.form_submit_button("追加")

    if submit:

        if task_name == "":
            st.error("タスク名を入力してください。")

        elif attachment == "":
            st.error("添付資料URLは必須です。")

        else:

            payload = {
                "task_name": task_name,
                "team": team,
                "assignee": assignee,
                "status": status,
                "progress": progress,
                "deadline": str(deadline),
                "attachment_url": attachment
            }

            if add_task(payload):
                st.success("追加しました！")
                st.rerun()


# -----------------------------
# Task List
# -----------------------------
st.divider()

st.header("タスク一覧")

df = load_tasks()

if not df.empty:

    editor = st.data_editor(

        df,

        hide_index=True,

        use_container_width=True,

        num_rows="fixed",

        column_config={

            "id": st.column_config.NumberColumn(
                disabled=True
            ),

            "status": st.column_config.SelectboxColumn(
                "ステータス",
                options=STATUS_OPTIONS,
            ),

            "progress": st.column_config.ProgressColumn(
                "進捗",
                min_value=0,
                max_value=100,
            ),

            "deadline": st.column_config.DateColumn(
                "期限"
            ),

            "updated_at": st.column_config.DatetimeColumn(
                disabled=True
            ),

            "attachment_url": st.column_config.LinkColumn(
                "添付資料"
            )

        },

        key="editor"
    )

    if st.button("変更を保存"):

        success = True

        for _, row in editor.iterrows():

            if not update_task(row.to_dict()):
                success = False

        if success:
            st.success("保存しました。")
            st.rerun()

else:
    st.info("まだタスクがありません。")
