import React from "react";
import { FiPlus, FiX } from "react-icons/fi";

export default function ChatSidebar({ chats, onNewChat, onSelect, current, onDeleteChat }) {
  const handleDelete = (e, idx) => {
    e.stopPropagation();
    onDeleteChat(idx);
  };

  return (
    <div className="w-64 bg-gray-100 border-r border-gray-300 h-full flex flex-col p-4 overflow-y-auto">
      <button
        className="flex items-center px-3 py-2 bg-white rounded-lg shadow-sm hover:bg-gray-100 text-sm font-medium"
        onClick={onNewChat}
      >
        <FiPlus className="mr-2" />
        新聊天
      </button>

      {chats.length > 0 && (
        <div className="text-gray-500 font-semibold text-sm mt-4 mb-2 px-1">聊天</div>
      )}

      <div className="space-y-1">
        {chats.map((chat, i) => (
          <div
            key={i}
            className={`flex justify-between items-center px-3 py-2 rounded text-sm cursor-pointer truncate ${
              i === current
                ? "bg-gray-300 text-black"
                : "bg-white hover:bg-gray-100 text-gray-700"
            }`}
            onClick={() => onSelect(i)}
          >
            <span className="truncate w-[85%]">
              {chat.title || chat.messages[0]?.text.slice(0, 20) || "新聊天"}
            </span>
            <FiX onClick={(e) => handleDelete(e, i)} className="text-gray-500 hover:text-red-500" />
          </div>
        ))}
      </div>
    </div>
  );
}
