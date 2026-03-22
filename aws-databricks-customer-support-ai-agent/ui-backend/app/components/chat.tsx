"use client";

import { useEffect, useState } from "react";
import Message from "./message";

export default function Chat({ selectedChat }: any) {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [followUps, setFollowUps] = useState<string[]>([]);

  const [currentChatId, setCurrentChatId] = useState<number | null>(null);
  const [chatTitle, setChatTitle] = useState<string>("New Chat");

  // ================= LOAD SELECTED CHAT =================
  useEffect(() => {
    if (selectedChat) {
      setMessages(selectedChat.messages);
      setCurrentChatId(selectedChat.id);
      setChatTitle(selectedChat.title || "New Chat");
    } else {
      setMessages([]);
      setCurrentChatId(null);
      setChatTitle("New Chat");
    }
  }, [selectedChat]);

  // ================= SAVE CHAT HISTORY =================
  useEffect(() => {
    if (messages.length === 0) return;

    const saved = localStorage.getItem("chat_history");
    let chats = saved ? JSON.parse(saved) : [];

    let chatId = currentChatId;

    if (!chatId) {
      chatId = Date.now();
      setCurrentChatId(chatId);

      chats.unshift({
        id: chatId,
        title: chatTitle,
        messages,
      });
    } else {
      chats = chats.map((c: any) =>
        c.id === chatId
          ? { ...c, messages, title: chatTitle }
          : c
      );
    }

    localStorage.setItem("chat_history", JSON.stringify(chats));
    window.dispatchEvent(new Event("chat_updated"));
  }, [messages, chatTitle]);

  // ================= GENERATE TITLE (ONLY ON FIRST MESSAGE) =================
  const generateTitle = async (firstMessage: string) => {
    try {
      const res = await fetch("/api/generate-title", {
        method: "POST",
        body: JSON.stringify({ message: firstMessage }),
      });

      const title = await res.text();
      setChatTitle(title);
    } catch {
      setChatTitle("New Chat");
    }
  };

  // ================= SEND MESSAGE =================
  const sendMessage = async (customInput?: string) => {
    const question = customInput || input;
    if (!question) return;

    if (messages.length === 0) {
      generateTitle(question);
    }

    const newMessages = [...messages, { role: "user", content: question }];
    setMessages(newMessages);
    setInput("");
    setLoading(true);
    setFollowUps([]);

    const res = await fetch("/api/chat", {
      method: "POST",
      body: JSON.stringify({
        question,
        history: messages.slice(-6),
      }),
    });

    const contentType = res.headers.get("content-type");

    // ================= SQL =================
    if (contentType?.includes("application/json")) {
      const data = await res.json();

      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content: data.answer,
          table: data.table,
        },
      ]);

      setFollowUps(data.followUps || []);
    } else {
      // ================= STREAMING =================
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      let assistantText = "";

      while (true) {
        const { done, value } = await reader!.read();
        if (done) break;

        const chunk = decoder.decode(value);

        if (chunk.includes("__FOLLOWUPS__")) {
          const [textPart, followPart] = chunk.split("__FOLLOWUPS__");

          assistantText += textPart;

          try {
            setFollowUps(JSON.parse(followPart));
          } catch {}
        } else {
          assistantText += chunk;
        }

        setMessages((prev) => {
          const base = [...prev.slice(0, newMessages.length)];
          return [
            ...base,
            { role: "assistant", content: assistantText },
          ];
        });
      }
    }

    setLoading(false);
  };

  // ================= UI =================
  return (
    <div className="flex-1 flex flex-col backdrop-blur-xl">
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((m, i) => (
          <Message
            key={i}
            content={m.content}
            role={m.role}
            table={m.table}
          />
        ))}

        {loading && (
          <div className="flex gap-3 items-center px-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-center text-sm font-bold">
              AI
            </div>

            <div className="flex gap-2">
              <div className="w-2 h-2 bg-white rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-white rounded-full animate-bounce delay-150" />
              <div className="w-2 h-2 bg-white rounded-full animate-bounce delay-300" />
            </div>
          </div>
        )}

        {followUps.length > 0 && (
          <div className="px-2 flex flex-wrap gap-2">
            {followUps.map((f, i) => (
              <button
                key={i}
                onClick={() => sendMessage(f)}
                className="text-sm px-3 py-1 rounded-full bg-indigo-500/20 hover:bg-indigo-500/40 transition border border-indigo-500/30"
              >
                {f}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="p-4 border-t border-white/10 bg-black/30 backdrop-blur-xl">
        <div className="flex gap-2 items-center bg-white/10 border border-white/10 rounded-xl px-3 py-2 focus-within:ring-2 focus-within:ring-indigo-500 transition">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask something..."
            className="flex-1 bg-transparent outline-none text-white placeholder:text-zinc-400"
            onKeyDown={(e) => {
              if (e.key === "Enter") sendMessage();
            }}
          />

          <button
            onClick={() => sendMessage()}
            className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 hover:opacity-90 transition text-sm font-medium"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
