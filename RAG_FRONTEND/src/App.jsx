// src/App.jsx
import React, { useState, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import ChatSidebar from "./components/ChatSidebar.jsx";
import ChatWindow from "./components/ChatWindow.jsx";
import { apiFetch } from "./utils/api.js";

export default function App() {
  const [chats, setChats] = useState([]);      // { id, title, messages }
  const [currentIdx, setCurrentIdx] = useState(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingMap, setLoadingMap] = useState({}); // { [chatId]: boolean }

  // 初次加载：拿列表
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

  // 点击侧边栏：加载完整历史
  const handleSelect = (idx) => {
    const chatId = chats[idx]?.id;
    if (!chatId) return;
    apiFetch(`chat/${chatId}`)
      .then((res) => res.json())
      .then((data) => {
        const messages = data.chat_history.map((m) => ({
          from: m.type === "user" ? "user" : "assistant",
          text: m.content,
        }));
        const firstUser = data.chat_history.find((m) => m.type === "user");
        const title = firstUser
          ? firstUser.content.slice(0, 20)
          : chats[idx].title;
        setChats((prev) => {
          const nxt = [...prev];
          nxt[idx] = { id: chatId, title, messages };
          return nxt;
        });
        setCurrentIdx(idx);
      })
      .catch((e) => console.error("加载聊天历史失败", e));
  };

  // ========= 重写 onSend，杜绝重复 =========
  const onSend = async (text) => {
    if (!text.trim()) return;

    // 1) 确定聊天索引和 ID，本地构造 updatedChats
    let idx = currentIdx;
    let updatedChats = [...chats];

    if (idx === null) {
      const newId = uuidv4();
      idx = updatedChats.length;
      updatedChats.push({
        id: newId,
        title: text.slice(0, 20),
        messages: [],
      });
      setCurrentIdx(idx);
    }

    const chatId = updatedChats[idx].id;
    // 防抖：如果正在加载，不重复
    if (loadingMap[chatId]) return;
    setLoadingMap((m) => ({ ...m, [chatId]: true }));

    // 2) 本地追加用户消息和 loading 提示
    updatedChats[idx].messages = [
      ...(updatedChats[idx].messages || []),
      { from: "user", text },
      { from: "assistant", text: "助手正在思考..." },
    ];
    setChats(updatedChats);

    // 3) 发请求
    try {
      const res = await apiFetch("chat/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: chatId, question: text }),
      });

      if (res.status === 429) {
        const err = await res.json();
        alert(err.error);
        // 保留用户消息，移除 loading
        updatedChats[idx].messages = updatedChats[idx].messages.filter(
          (m) => m.text !== "助手正在思考..."
        );
        setChats([...updatedChats]);
      } else if (!res.ok) {
        throw new Error(res.status);
      } else {
        const data = await res.json();
        // 4) 替换 loading 为真实回复
        updatedChats[idx].messages = updatedChats[idx].messages.filter(
          (m) => m.text !== "助手正在思考..."
        );
        updatedChats[idx].messages.push({ from: "assistant", text: data.reply || "" });
        setChats([...updatedChats]);
      }
    } catch (e) {
      console.error("发送失败", e);
      // 出错时只移除 loading
      updatedChats[idx].messages = updatedChats[idx].messages.filter(
        (m) => m.text !== "助手正在思考..."
      );
      setChats([...updatedChats]);
    } finally {
      setLoadingMap((m) => ({ ...m, [chatId]: false }));
    }
  };
  // ======== onSend end ========

  const onNewChat = () => setCurrentIdx(null);
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
