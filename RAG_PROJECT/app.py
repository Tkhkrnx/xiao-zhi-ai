import sqlite3
import time
from flask import Flask, request, jsonify, g
from graph2.graph_2 import graph  # 你的工作流graph对象

app = Flask(__name__)
DB_PATH = 'chat_sessions.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        c = db.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            created_at INTEGER
        )
        ''')
        c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            type TEXT,
            content TEXT,
            created_at INTEGER,
            FOREIGN KEY(chat_id) REFERENCES chats(id)
        )
        ''')
        db.commit()

def load_chat_history(chat_id):
    db = get_db()
    c = db.cursor()
    c.execute('SELECT type, content FROM messages WHERE chat_id = ? ORDER BY created_at ASC', (chat_id,))
    rows = c.fetchall()
    return [{"type": row["type"], "content": row["content"]} for row in rows]

def save_chat_message(chat_id, msg_type, content):
    db = get_db()
    c = db.cursor()
    now = int(time.time())
    c.execute(
        'INSERT INTO messages (chat_id, type, content, created_at) VALUES (?, ?, ?, ?)',
        (chat_id, msg_type, content, now)
    )
    db.commit()

def ensure_chat_exists(chat_id):
    db = get_db()
    c = db.cursor()
    c.execute('SELECT 1 FROM chats WHERE id = ?', (chat_id,))
    if c.fetchone() is None:
        c.execute('INSERT INTO chats (id, created_at) VALUES (?, ?)', (chat_id, int(time.time())))
        db.commit()

@app.route("/api/chat/list", methods=["GET"])
def api_chat_list():
    """
    返回所有聊天会话列表，并附带第一条用户消息作为 preview
    """
    db = get_db()
    c = db.cursor()
    c.execute('''
      SELECT c.id AS chat_id,
             c.created_at,
             (
               SELECT content
               FROM messages
               WHERE chat_id = c.id AND type = 'user'
               ORDER BY created_at ASC
               LIMIT 1
             ) AS preview
      FROM chats c
      ORDER BY c.created_at DESC
    ''')
    rows = c.fetchall()
    chats = [
        {
            "chat_id": row["chat_id"],
            "created_at": row["created_at"],
            "preview": row["preview"] or ""
        }
        for row in rows
    ]
    return jsonify(chats)

@app.route("/api/chat/<chat_id>", methods=["GET"])
def api_chat_detail(chat_id):
    """
    返回单个会话的完整历史
    """
    ensure_chat_exists(chat_id)
    chat_history = load_chat_history(chat_id)
    return jsonify({
        "chat_id": chat_id,
        "chat_history": chat_history
    })

@app.route("/api/chat/send", methods=["POST"])
def api_chat_send():
    """
    接收用户输入，执行 RAG 工作流，保存消息，并返回助手回复和最新历史
    """
    data = request.json
    session_id = data.get("session_id", "default")
    question = data.get("question")
    if not question:
        return jsonify({"error": "question is required"}), 400

    ensure_chat_exists(session_id)
    chat_history = load_chat_history(session_id)

    # 执行工作流
    inputs = {"question": question, "chat_history": chat_history}
    final_state = None
    for output in graph.stream(inputs, {"recursion_limit": 50}):
        final_state = list(output.values())[-1]

    # 保存用户和助手消息
    save_chat_message(session_id, "user", question)
    if "generation" in final_state:
        save_chat_message(session_id, "assistant", final_state["generation"])

    new_history = load_chat_history(session_id)
    return jsonify({
        "reply": final_state.get("generation", ""),
        "chat_history": new_history
    })

@app.route("/api/chat/<chat_id>", methods=["DELETE"])
def api_chat_delete(chat_id):
    """
    删除某个会话及其所有消息
    """
    db = get_db()
    c = db.cursor()
    c.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
    c.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
    db.commit()
    return jsonify({"status": "success", "deleted_chat_id": chat_id})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000)
