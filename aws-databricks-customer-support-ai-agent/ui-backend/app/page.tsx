"use client";

import Chat from "@/components/chat";
import Sidebar from "@/components/sidebar";
import { useState } from "react";

export default function Page() {
  const [selectedChat, setSelectedChat] = useState<any>(null);

  return (
    <div className="flex h-screen bg-gradient-to-br from-zinc-950 via-black to-zinc-900 text-white">
      <Sidebar onSelectChat={setSelectedChat} />
      <Chat selectedChat={selectedChat} />
    </div>
  );
}