import React, { useState, useEffect } from "react";
import { FiPlus, FiX, FiChevronLeft, FiChevronRight } from "react-icons/fi";

export default function ChatSidebar({ chats, onNewChat, onSelect, current, onDeleteChat }) {
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    if (window.innerWidth < 640) {
      setCollapsed(true);
    }
  }, []);

  const handleDelete = (e, idx) => {
    e.stopPropagation();
    onDeleteChat(idx);
  };

  return (
    <div
      className={`
        h-full flex flex-col border-r border-gray-300 bg-gray-100
        transition-[width] duration-300 ease-in-out
        overflow-hidden
        ${collapsed ? "w-16" : "w-64"}
        sm:w-64
      `}
    >
      <div className="flex items-center mb-4 p-2">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 bg-white rounded-lg shadow-sm hover:bg-gray-100"
          title={collapsed ? "展开侧边栏" : "收起侧边栏"}
        >
          {collapsed ? <FiChevronRight /> : <FiChevronLeft />}
        </button>

        <div
          className={`
            ml-2 transition-all duration-300 ease-in-out
            ${collapsed ? "opacity-0 translate-x-[-10px] pointer-events-none" : "opacity-100 translate-x-0"}
          `}
        >
          <button
            className="flex items-center px-3 py-2 bg-white rounded-lg shadow-sm hover:bg-gray-100 text-sm font-medium"
            onClick={onNewChat}
          >
            <FiPlus className="mr-2" />
            新聊天
          </button>
        </div>
      </div>

      {!collapsed && chats.length > 0 && (
        <div className="text-gray-500 font-semibold text-sm mb-2 px-3 select-none transition-opacity duration-300">
          聊天
        </div>
      )}

      <div className="space-y-1 flex-1 overflow-y-auto px-2">
        {chats.map((chat, i) => (
          <div
            key={i}
            className={`
              flex justify-between items-center py-2 px-3 rounded text-sm cursor-pointer truncate transition-all duration-300
              ${i === current
                ? "bg-gray-300 text-black"
                : "bg-white hover:bg-gray-100 text-gray-700"}
            `}
            onClick={() => onSelect(i)}
            title={chat.title || chat.messages[0]?.text.slice(0, 20) || "新聊天"}
          >
            <span className={`truncate ${collapsed ? "w-0" : "w-[85%]"} transition-all duration-300`}>
              {chat.title || chat.messages[0]?.text.slice(0, 20) || "新聊天"}
            </span>
            {!collapsed && (
              <FiX
                onClick={(e) => handleDelete(e, i)}
                className="text-gray-500 hover:text-red-500"
                title="删除聊天"
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
