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
  const [collapsed, setCollapsed] = useState(window.innerWidth < 768);
  const activeSessionId = useRef(null);

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

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setCollapsed(true);
      } else {
        setCollapsed(false);
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const handleSelect = (idx) => {
    const chatId = chats[idx]?.id;
    if (!chatId) return;
    activeSessionId.current = chatId;

    apiFetch(`chat/${chatId}`)
      .then((res) => res.json())
      .then((data) => {
        const messages = data.chat_history.map((m) => ({
          from: m.type === "user" ? "user" : "assistant",
          text: m.content,
        }));

        if (loadingMap[chatId]) {
          messages.push({ from: "assistant", text: "助手正在思考..." });
        }

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
    activeSessionId.current = chatId;

    if (loadingMap[chatId]) return;

    setLoadingMap((m) => ({ ...m, [chatId]: true }));

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
    return (
      <div className="flex items-center justify-center h-screen text-gray-500 dark:text-gray-400">
        加载中...
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <ChatSidebar
        chats={chats}
        onNewChat={onNewChat}
        onSelect={handleSelect}
        onDeleteChat={onDeleteChat}
        current={currentIdx}
        collapsed={collapsed}
        onCollapseChange={setCollapsed}
      />

      <main
        className={`flex-grow flex flex-col
          transition-all duration-300
          ${collapsed ? "w-[calc(100%-56px)] mx-auto" : "w-[calc(100%-256px)]"}`}
        style={{ maxWidth: collapsed ? "calc(100% - 56px)" : "calc(100% - 256px)" }}
      >
        {currentIdx === null ? (
          <div className="flex-grow flex items-center justify-center text-gray-500 dark:text-gray-400 px-4 text-center">
            <p>
              在下方输入你的问题，或点击左侧“新聊天”开始。
            </p>
          </div>
        ) : (
          <ChatWindow
            chat={chats[currentIdx]}
            onSend={onSend}
            loading={loadingMap[chats[currentIdx].id]}
          />
        )}
      </main>
    </div>
  );
}
