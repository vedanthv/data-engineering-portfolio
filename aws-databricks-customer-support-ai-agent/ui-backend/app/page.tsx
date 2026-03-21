"use client";

import { useState, useRef, useEffect,JSX } from "react";
import { motion } from "framer-motion";
import { Send, Bot, User, Copy, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";

export default function Home() {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const sendMessage = async (customInput?: string) => {
    const text = customInput || input;
    if (!text.trim()) return;

    const userMsg = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text }), // ✅ UNCHANGED
      });

      if (!res.body) throw new Error("No response body");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      let assistantMsg = { role: "assistant", content: "" };
      setMessages((prev) => [...prev, assistantMsg]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        assistantMsg.content += chunk;

        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = { ...assistantMsg };
          return updated;
        });
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error fetching response" },
      ]);
    }

    setLoading(false);
  };

  const copyText = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const renderContent = (content: string): JSX.Element => {
    try {
      const parsed = JSON.parse(content);

      if (
        (parsed.type === "table" && parsed.data) ||
        (Array.isArray(parsed) && parsed.length > 0)
      ) {
        const tableData = parsed.type === "table" ? parsed.data : parsed;

        return (
          <div className="space-y-3">
            {parsed.sql && (
              <pre className="text-xs bg-black border border-gray-700 p-3 rounded-lg overflow-x-auto">
                {parsed.sql}
              </pre>
            )}

            {tableData.length === 0 ? (
              <p className="text-xs text-gray-400">No data found</p>
            ) : (
              <div className="overflow-x-auto rounded-xl border border-gray-800">
                <table className="w-full text-xs">
                  <thead className="bg-gray-800 text-gray-300">
                    <tr>
                      {Object.keys(tableData[0]).map((key) => (
                        <th key={key} className="p-3 text-left">
                          {key}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {tableData.map((row: any, i: number) => (
                      <tr
                        key={i}
                        className="border-t border-gray-800 hover:bg-gray-900"
                      >
                        {Object.values(row).map((val: any, j: number) => (
                          <td key={j} className="p-3">
                            {val}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        );
      }
    } catch {}

    return (
      <ReactMarkdown
        components={{
          p: ({ children }) => <p className="mb-2">{children}</p>,
          strong: ({ children }) => (
            <strong className="font-semibold text-white">
              {children}
            </strong>
          ),
          li: ({ children }) => (
            <li className="ml-4 list-disc">{children}</li>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    );
  };

  const suggestions = [
    "Top 5 customers by revenue",
    "Orders in last 7 days",
    "Average order value",
    "Show failed orders",
  ];

  return (
    <div className="flex h-screen bg-black text-white">
      {/* Sidebar */}
      <div className="hidden md:flex w-64 border-r border-gray-800 p-4 flex-col">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Sparkles size={16} /> AI Assistant
        </h2>

        <div className="space-y-2">
          {suggestions.map((s, i) => (
            <button
              key={i}
              onClick={() => sendMessage(s)}
              className="w-full text-left text-sm p-2 rounded-lg bg-gray-900 hover:bg-gray-800 transition"
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Main */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-800 p-4">
          <h1 className="font-semibold">Orders AI</h1>
        </div>

        {/* Chat */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4 max-w-4xl mx-auto w-full">
          {messages.map((m, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-3 ${
                m.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {m.role === "assistant" && (
                <div className="p-2 bg-gray-800 rounded-full">
                  <Bot size={16} />
                </div>
              )}

              <div className="relative group max-w-[75%]">
                <div
                  className={`px-4 py-3 rounded-2xl text-sm shadow ${
                    m.role === "user"
                      ? "bg-white text-black"
                      : "bg-gray-900 border border-gray-800"
                  }`}
                >
                  {renderContent(m.content)}
                </div>

                {m.role === "assistant" && (
                  <div className="absolute -bottom-6 right-2 hidden group-hover:flex gap-2 text-gray-400">
                    <Copy
                      size={14}
                      className="cursor-pointer hover:text-white"
                      onClick={() => copyText(m.content)}
                    />
                  </div>
                )}
              </div>

              {m.role === "user" && (
                <div className="p-2 bg-gray-800 rounded-full">
                  <User size={16} />
                </div>
              )}
            </motion.div>
          ))}

          {loading && (
            <div className="text-gray-500 text-sm animate-pulse">
              Thinking...
            </div>
          )}

          <div ref={bottomRef}></div>
        </div>

        {/* Input */}
        <div className="border-t border-gray-800 p-4 bg-black sticky bottom-0">
          <div className="max-w-4xl mx-auto flex gap-2">
            <input
              ref={inputRef}
              className="flex-1 bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-white"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              placeholder="Ask about orders..."
            />

            <button
              disabled={loading}
              onClick={() => sendMessage()}
              className="bg-white text-black px-4 py-3 rounded-xl hover:scale-105 transition"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}