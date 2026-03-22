import { NextRequest } from "next/server";
import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY!,
});

export async function POST(req: NextRequest) {
  const { table } = await req.json();

  const prompt = `
Analyze this dataset and give business insights:

- Trends
- Anomalies
- Recommendations

Data:
${JSON.stringify(table)}
`;

  const res = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [{ role: "user", content: prompt }],
  });

  return new Response(res.choices[0].message.content);
}