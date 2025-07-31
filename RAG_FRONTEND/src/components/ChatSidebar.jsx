import React, { useState, useEffect } from "react";
import { FiPlus, FiX, FiChevronLeft, FiChevronRight } from "react-icons/fi";

export default function ChatSidebar({ chats, onNewChat, onSelect, current, onDeleteChat }) {
  const [collapsed, setCollapsed] = useState(window.innerWidth < 768);

  // 自动监听窗口大小，小屏默认折叠
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setCollapsed(true);
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const handleDelete = (e, idx) => {
    e.stopPropagation();
    onDeleteChat(idx);
  };

  return (
    <div
      className={`
        relative h-full flex flex-col border-r border-gray-300 dark:border-gray-700
        bg-gray-100 dark:bg-gray-800 transition-all duration-300 ease-in-out
        ${collapsed ? "w-14" : "w-64"}
      `}
    >
      {/* 折叠/展开按钮（垂直居中） */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute right-[-12px] top-1/2 transform -translate-y-1/2 z-20
                   bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 
                   rounded-full p-1 shadow-md"
        title={collapsed ? "展开侧边栏" : "收起侧边栏"}
      >
        {collapsed ? <FiChevronRight /> : <FiChevronLeft />}
      </button>

      {/* 新聊天按钮 */}
      <div className="flex items-center mb-4 p-2 pt-4">
        <div
          className={`
            transition-all duration-300 ease-in-out
            ${collapsed ? "opacity-0 translate-x-[-10px] pointer-events-none" : "opacity-100 translate-x-0"}
          `}
        >
          <button
            className="flex items-center px-3 py-2 bg-white dark:bg-gray-700 text-black dark:text-white 
                       rounded-lg shadow-sm hover:bg-gray-100 dark:hover:bg-gray-600 text-sm font-medium"
            onClick={onNewChat}
          >
            <FiPlus className="mr-2" />
            新聊天
          </button>
        </div>
      </div>

      {/* 聊天标题 */}
      {!collapsed && chats.length > 0 && (
        <div className="text-gray-500 dark:text-gray-300 font-semibold text-sm mb-2 px-3 select-none transition-opacity duration-300">
          聊天
        </div>
      )}

      {/* 聊天列表 */}
      <div className="space-y-1 flex-1 overflow-y-auto px-2">
        {chats.map((chat, i) => (
          <div
            key={i}
            className={`
              flex justify-between items-center py-2 px-3 rounded text-sm cursor-pointer truncate
              transition-all duration-300
              ${i === current
                ? "bg-gray-300 dark:bg-gray-600 text-black dark:text-white"
                : "bg-white dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200"}
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
