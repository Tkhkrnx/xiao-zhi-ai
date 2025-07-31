// src/App.jsx
import React, { useState, useEffect, useRef } from "react";
import { v4 as uuidv4 } from "uuid";
import ChatSidebar from "./components/ChatSidebar.jsx";
import ChatWindow from "./components/ChatWindow.jsx";
import { apiFetch } from "./utils/api.js";

export default function App() {
  const [chats, setChats] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingMap, setLoadingMap] = useState({});
  const activeSessionId = useRef(null); // 👈 保留当前激活聊天 ID

  // 初次加载聊天列表
  useEffect(() => {
    apiFetch("chat/list")
      .then((res) => res.json())
      .then((data) => {
        const formatted = data.map((item) => ({
          id: item.chat_id,
          title: (item.preview || item.chat_id).slice(0, 20),
          messages: [],
        }));
        setChats(formatted);
      })
      .catch((e) => console.error("加载聊天列表失败", e))
      .finally(() => setLoadingList(false));
  }, []);

  // 选择聊天，加载历史记录
  const handleSelect = (idx) => {
    const chatId = chats[idx]?.id;
    if (!chatId) return;
    activeSessionId.current = chatId; // 👈 更新激活会话 ID

    apiFetch(`chat/${chatId}`)
      .then((res) => res.json())
      .then((data) => {
        const messages = data.chat_history.map((m) => ({
          from: m.type === "user" ? "user" : "assistant",
          text: m.content,
        }));
        const firstUser = data.chat_history.find((m) => m.type === "user");
        const title = firstUser ? firstUser.content.slice(0, 20) : chats[idx].title;

        setChats((prev) => {
          const newChats = [...prev];
          newChats[idx] = { id: chatId, title, messages };
          return newChats;
        });
        setCurrentIdx(idx);
      })
      .catch((e) => console.error("加载聊天历史失败", e));
  };

  const onSend = async (text) => {
    if (!text.trim()) return;

    let idx = currentIdx;
    let updatedChats = [...chats];
    let newId = null;

    if (idx === null) {
      newId = uuidv4();
      idx = updatedChats.length;
      updatedChats.push({ id: newId, title: text.slice(0, 20), messages: [] });
      setChats(updatedChats);
      setCurrentIdx(idx);
    }

    const chatId = updatedChats[idx].id;
    activeSessionId.current = chatId; // 👈 更新激活会话 ID

    if (loadingMap[chatId]) return;

    setLoadingMap((m) => ({ ...m, [chatId]: true }));

    // 先显示用户输入与 loading 状态
    setChats((prev) => {
      const newChats = [...prev];
      newChats[idx].messages = [
        ...(newChats[idx].messages || []),
        { from: "user", text },
        { from: "assistant", text: "助手正在思考..." },
      ];
      return newChats;
    });

    try {
      const res = await apiFetch("chat/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: chatId, question: text }),
      });

      if (res.status === 429) {
        const err = await res.json();
        alert(err.error);
        setChats((prev) => {
          const newChats = [...prev];
          newChats[idx].messages = newChats[idx].messages.filter(
            (m) => m.text !== "助手正在思考..."
          );
          return newChats;
        });
      } else if (!res.ok) {
        throw new Error(res.status);
      } else {
        const data = await res.json();
        // ✅ 响应成功后立即更新对应聊天内容（根据 session_id 判断）
        setChats((prev) => {
          const newChats = [...prev];
          const targetIdx = newChats.findIndex((c) => c.id === chatId);
          if (targetIdx !== -1) {
            newChats[targetIdx].messages = newChats[targetIdx].messages.filter(
              (m) => m.text !== "助手正在思考..."
            );
            newChats[targetIdx].messages.push({
              from: "assistant",
              text: data.reply || "",
            });
          }
          return newChats;
        });
      }
    } catch (e) {
      console.error("发送失败", e);
      setChats((prev) => {
        const newChats = [...prev];
        const targetIdx = newChats.findIndex((c) => c.id === chatId);
        if (targetIdx !== -1) {
          newChats[targetIdx].messages = newChats[targetIdx].messages.filter(
            (m) => m.text !== "助手正在思考..."
          );
        }
        return newChats;
      });
    } finally {
      setLoadingMap((m) => ({ ...m, [chatId]: false }));
    }
  };

  const onNewChat = () => {
    setCurrentIdx(null);
    activeSessionId.current = null;
  };

  const onDeleteChat = async (idx) => {
    const chatId = chats[idx]?.id;
    if (!chatId) return;

    try {
      await apiFetch(`chat/${chatId}`, { method: "DELETE" });
      setChats((prev) => prev.filter((_, i) => i !== idx));
      if (currentIdx === idx) setCurrentIdx(null);
      else if (currentIdx > idx) setCurrentIdx((c) => c - 1);
    } catch (e) {
      console.error("删除失败", e);
    }
  };

  if (loadingList) {
    return <div className="flex justify-center items-center h-screen">加载中...</div>;
  }

  return (
    <div className="h-screen flex bg-white dark:bg-gray-900">
      <ChatSidebar
        chats={chats}
        onNewChat={onNewChat}
        onSelect={handleSelect}
        onDeleteChat={onDeleteChat}
        current={currentIdx}
      />
      <div className="flex-1 flex justify-center overflow-hidden">
        <div className="w-full max-w-4xl flex flex-col">
          <ChatWindow chat={currentIdx !== null ? chats[currentIdx] : null} onSend={onSend} />
        </div>
      </div>
    </div>
  );
}
