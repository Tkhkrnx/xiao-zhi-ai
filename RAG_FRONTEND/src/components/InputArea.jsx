import React, { useState, useRef, useEffect } from "react";
import sendIcon from "/send.svg";

export default function InputArea({ onSend, isNew }) {
  const [text, setText] = useState("");
  const [focused, setFocused] = useState(false);
  const textareaRef = useRef();

  const handleSend = () => {
    const trimmed = text.trim();
    if (trimmed) {
      onSend(trimmed);
      setText("");
      setFocused(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  useEffect(() => {
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = "auto";
      const newHeight = Math.min(ta.scrollHeight, 200);
      ta.style.height = newHeight + "px";
      ta.style.overflowY = ta.scrollHeight > 200 ? "auto" : "hidden";
    }
  }, [text]);

  return (
    <div
      className={`w-full ${
        isNew ? "max-w-xl mx-auto mt-2" : "max-w-3xl mx-auto pt-2"
      }`}
    >
      <div className="relative">
        <textarea
          ref={textareaRef}
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(text !== "")}
          placeholder={
            focused || text
              ? ""
              : "询问任何问题"
          }
          style={{
            minHeight: "120px",
            maxHeight: "200px",
            paddingRight: "56px", // 为按钮预留空间
            paddingTop: "16px",
            paddingBottom: "16px",
            borderRadius: "28px",
            resize: "none",
          }}
          className="w-full text-base leading-relaxed px-4 border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white placeholder-gray-400 dark:bg-gray-800 dark:border-gray-600 dark:placeholder-gray-500 dark:text-gray-100"
        />
        <button
          onClick={handleSend}
          className="absolute right-4 bottom-4 w-9 h-9 bg-black rounded-full flex items-center justify-center hover:opacity-80 transition-opacity"
          aria-label="发送"
          style={{
            right: "16px",   // 与 paddingRight 一致
            bottom: "16px",  // 与 paddingBottom 一致
          }}
        >
          <img src={sendIcon} alt="发送" className="w-4 h-4 invert" />
        </button>
      </div>
    </div>
  );
}
