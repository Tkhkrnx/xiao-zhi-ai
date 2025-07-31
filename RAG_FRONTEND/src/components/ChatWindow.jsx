import React, { useState, useEffect, useRef } from "react";

export default function ChatWindow({ chat, onSend, loading }) {
  const [input, setInput] = useState("");
  const inputRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    setInput("");
  }, [chat.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat.messages]);

  const handleSend = () => {
    if (!input.trim()) return;
    onSend(input.trim());
    setInput("");
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full p-4">
      <div className="flex-grow overflow-y-auto mb-4 space-y-4">
        {chat.messages.map((msg, i) => (
          <div
            key={i}
            className={`max-w-3xl px-4 py-2 rounded-lg whitespace-pre-wrap
              ${msg.from === "user"
                ? "bg-gray-200 dark:bg-gray-700 self-end text-gray-900 dark:text-gray-100"
                : "bg-gray-300 dark:bg-gray-600 self-start text-gray-900 dark:text-gray-100"
              }
            `}
            style={{ wordBreak: "break-word" }}
          >
            {msg.text}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="flex items-center space-x-2">
        <textarea
          ref={inputRef}
          className="flex-grow resize-none rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={2}
          placeholder="输入消息，按回车发送，Shift+回车换行"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={loading}
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className={`p-2 rounded-md bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors`}
          aria-label="发送消息"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-6 w-6 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10l9-6 9 6-9 6-9-6z" />
          </svg>
        </button>
      </div>
    </div>
  );
}
