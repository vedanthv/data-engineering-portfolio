import { NextRequest } from "next/server";
import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY!,
});

function cleanTitle(text: string) {
  return text
    .replace(/<!DOCTYPE[^>]*>/gi, "")
    .replace(/<script[^>]*>.*?<\/script>/gi, "")
    .replace(/<style[^>]*>.*?<\/style>/gi, "")
    .replace(/<[^>]+>/g, "") // remove all HTML
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/[*_"'`]/g, "")
    .replace(/[^\w\s]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .split(" ")
    .slice(0, 5)
    .join(" ");
}

export async function POST(req: NextRequest) {
  const { message } = await req.json();

  const prompt = `
Generate a short chat title (max 5 words).

Rules:
- Be concise and clear
- No punctuation
- No quotes
- No emojis

User message:
${message}
`;

  const res = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [{ role: "user", content: prompt }],
  });

  const rawTitle = res.choices[0].message.content?.trim() || "New Chat";

  const title = cleanTitle(rawTitle);

  return new Response(title, {
    headers: { "Content-Type": "text/plain" },
  });
}