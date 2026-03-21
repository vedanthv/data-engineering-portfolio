import axios from "axios";

const OPENAI_API_KEY = process.env.OPENAI_API_KEY!;

export async function callLLM(messages: any[]) {
  const res = await axios.post(
    "https://api.openai.com/v1/chat/completions",
    {
      model: "gpt-4o-mini",
      messages,
      temperature: 0,
    },
    {
      headers: {
        Authorization: `Bearer ${OPENAI_API_KEY}`,
      },
    }
  );

  return res.data.choices[0].message.content;
}