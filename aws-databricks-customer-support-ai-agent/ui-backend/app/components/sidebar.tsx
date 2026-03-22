"use client";

import { useEffect, useState } from "react";

export default function Sidebar({ onSelectChat }: any) {
  const [chats, setChats] = useState<any[]>([]);

  useEffect(() => {
    const load = () => {
      const saved = localStorage.getItem("chat_history");
      if (saved) setChats(JSON.parse(saved));
      else setChats([]);
    };

    load();

    window.addEventListener("storage", load);
    window.addEventListener("chat_updated", load);

    return () => {
      window.removeEventListener("storage", load);
      window.removeEventListener("chat_updated", load);
    };
  }, []);

  const handleSelect = (chat: any) => {
    onSelectChat(chat);
  };

  const newChat = () => {
    onSelectChat(null);
    window.dispatchEvent(new Event("chat_updated"));
  };

  const clearHistory = () => {
    const confirmClear = confirm("Are you sure you want to clear all chats?");
    if (!confirmClear) return;

    localStorage.removeItem("chat_history");
    setChats([]);
    onSelectChat(null);

    window.dispatchEvent(new Event("chat_updated")); 
  };

  return (
    <div className="w-72 bg-white/5 backdrop-blur-xl border-r border-white/10 p-4 flex flex-col">
      <div className="space-y-2 mb-4">
        <button
          onClick={newChat}
          className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 py-2 rounded-xl font-medium hover:opacity-90 transition"
        >
          + New Chat
        </button>

        <button
          onClick={clearHistory}
          className="w-full bg-red-500/20 border border-red-500/30 text-red-300 py-2 rounded-xl hover:bg-red-500/30 transition"
        >
          Clear History
        </button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-2">
        {chats.length === 0 && (
          <div className="text-sm text-zinc-400 text-center mt-10">
            No chats yet
          </div>
        )}

        {chats.map((chat, i) => (
          <div
            key={i}
            onClick={() => handleSelect(chat)}
            className="p-3 rounded-xl cursor-pointer hover:bg-white/10 transition truncate"
          >
            {chat.title || "Untitled Chat"}
          </div>
        ))}
      </div>
    </div>
  );
}