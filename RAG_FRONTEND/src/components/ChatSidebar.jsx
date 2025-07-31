import React from "react";
import {
  FiPlus,
  FiTrash2,
  FiChevronLeft,
  FiChevronRight,
} from "react-icons/fi";

export default function ChatSidebar({
  chats,
  onNewChat,
  onSelect,
  current,
  onDeleteChat,
  collapsed,
  onCollapseChange,
}) {
  return (
    <div
      className={`h-screen flex flex-col bg-gray-100 dark:bg-gray-800 border-r border-gray-300 dark:border-gray-700
        flex-shrink-0
        transition-width duration-300
        ${collapsed ? "w-14" : "w-64"}`}
    >
      <div className="flex items-center justify-between px-3 h-14 border-b border-gray-300 dark:border-gray-700">
        {!collapsed && <h2 className="font-semibold text-gray-700 dark:text-gray-200">聊天</h2>}
        <button
          onClick={() => onCollapseChange(!collapsed)}
          className="p-1 rounded hover:bg-gray-300 dark:hover:bg-gray-700 focus:outline-none"
          aria-label={collapsed ? "展开侧边栏" : "收起侧边栏"}
        >
          {collapsed ? <FiChevronRight size={20} /> : <FiChevronLeft size={20} />}
        </button>
      </div>

      <div className="flex-1 overflow-auto">
        {chats.length === 0 && !collapsed && (
          <p className="text-center text-gray-500 mt-4 px-2">暂无聊天，点击“新聊天”开始</p>
        )}
        <ul>
          {chats.map((chat, idx) => (
            <li
              key={chat.id}
              className={`flex items-center justify-between cursor-pointer px-3 py-2 select-none
                ${
                  idx === current
                    ? "bg-gray-300 dark:bg-gray-700"
                    : "hover:bg-gray-200 dark:hover:bg-gray-600"
                }
                ${collapsed ? "justify-center" : ""}
              `}
              onClick={() => onSelect(idx)}
              title={chat.title}
            >
              {!collapsed && (
                <span className="truncate" style={{ maxWidth: "calc(100% - 24px)" }}>
                  {chat.title}
                </span>
              )}
              {collapsed && (
                <span className="text-gray-500 dark:text-gray-400 text-sm">
                  {chat.title.slice(0, 2)}
                </span>
              )}

              {!collapsed && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteChat(idx);
                  }}
                  className="text-gray-500 hover:text-red-600 dark:hover:text-red-400"
                  aria-label="删除聊天"
                >
                  <FiTrash2 />
                </button>
              )}
            </li>
          ))}
        </ul>
      </div>

      <div className="border-t border-gray-300 dark:border-gray-700 p-3">
        <button
          onClick={onNewChat}
          className="flex items-center justify-center w-full px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={collapsed}
        >
          <FiPlus className="mr-2" />
          新聊天
        </button>
      </div>
    </div>
  );
}
