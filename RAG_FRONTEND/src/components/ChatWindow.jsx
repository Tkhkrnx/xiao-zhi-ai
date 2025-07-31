// src/components/ChatWindow.jsx
import React, { useEffect, useRef } from "react";
import InputArea from "./InputArea.jsx";
import ReactMarkdown from "react-markdown";

export default function ChatWindow({ chat, onSend }) {
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat]);

  const isNew = !chat || !chat.messages || chat.messages.length === 0;

  const isThinkingMessage = (msg) =>
    msg.from === "assistant" && msg.text?.trim() === "助手正在思考...";

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900">
      {isNew ? (
        <div className="flex flex-col justify-center items-center flex-grow px-6">
          <h1 className="text-2xl font-medium text-gray-800 dark:text-gray-100 mb-6">
            有什么可以帮忙的？
          </h1>
          <InputArea onSend={onSend} isNew />
        </div>
      ) : (
        <>
          <div className="flex-grow overflow-y-auto px-4 py-6 space-y-4">
            {chat.messages.map((msg, i) => {
              if (msg.from === "assistant") {
                if (isThinkingMessage(msg)) {
                  return (
                    <p
                      key={i}
                      className="text-center italic text-gray-500 dark:text-gray-400 whitespace-pre-wrap"
                    >
                      助手正在思考...
                    </p>
                  );
                }

                return (
                  <div
                    key={i}
                    className="prose dark:prose-invert mx-auto max-w-none whitespace-pre-wrap"
                  >
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  </div>
                );
              } else {
                return (
                  <div key={i} className="flex justify-end">
                    <div className="bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg px-4 py-2 max-w-[70%] whitespace-pre-wrap">
                      {msg.text}
                    </div>
                  </div>
                );
              }
            })}
            <div ref={messagesEndRef} />
          </div>

          <div className="w-full px-4 pb-4 bg-white dark:bg-gray-900">
            <InputArea onSend={onSend} />
          </div>
        </>
      )}
    </div>
  );
}
