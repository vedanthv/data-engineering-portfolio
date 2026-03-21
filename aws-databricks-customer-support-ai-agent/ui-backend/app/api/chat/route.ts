import { NextRequest } from "next/server";
import { vectorSearch } from "@/lib/databricks";
import { callLLM } from "@/lib/llm";
import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY!,
});

// Detect aggregation queries
function isAggregationQuery(q: string) {
  const keywords = [
    "total",
    "sum",
    "average",
    "avg",
    "count",
    "group by",
    "revenue",
    "top",
    "trend",
  ];
  return keywords.some((k) => q.toLowerCase().includes(k));
}

// Clean SQL output
function cleanSQL(sql: string) {
  return sql
    .replace(/```sql/g, "")
    .replace(/```/g, "")
    .replace(/^sql\s*/i, "")
    .trim();
}

function formatAnswer(text: string) {
  let cleaned = text.trim();

  try {
    const parsed = JSON.parse(cleaned);

    if (Array.isArray(parsed) && parsed.length > 0) {
      return JSON.stringify({
        type: "table",
        data: parsed,
      });
    }
  } catch (e) {
    // not JSON → continue
  }

  if (cleaned.includes("|") && cleaned.includes("\n")) {
    return cleaned;
  }

  cleaned = cleaned
    .replace(/\. /g, ".\n\n")
    .replace(/- /g, "\n• ")
    .trim();

  return cleaned;
}

// Generate SQL
async function generateSQL(question: string) {
  const prompt = `
You are a SQL generator.

STRICT RULES:
- Use ONLY these columns:
  - order_id
  - customer_id
  - product_id
  - order_status
  - order_amount
  - currency
  - payment_method
  - payment_status
  - shipping_address
  - billing_address
  - order_date
  - delivery_date
  - discount
  - tax
  - shipping_cost
  - quantity
  - seller_id
  - warehouse_id
  - region
  - city
  - pincode
  - device_type
  - browser
  - ip_address
  - is_gift
  - gift_message
  - coupon_code
  - loyalty_points_used
  - order_channel
  - fulfillment_type
  - delivery_partner
  - status_timestamp
  - created_at
  - updated_at
  - year
  - month
  - day

- IMPORTANT:
  - Always return multiple rows where applicable
  - For aggregations, include grouping if meaningful
  - Example:
    - "revenue by month" → GROUP BY month
    - "top customers" → ORDER BY + LIMIT

- Return ONLY SQL

Table: customer_suppport_agent.raw.orders

Question: ${question}
`;

  const res = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [{ role: "user", content: prompt }],
  });

  return cleanSQL(res.choices[0].message.content!);
}

// Run SQL on Databricks
async function runSQL(query: string) {
  const res = await fetch(process.env.DATABRICKS_SQL_URL!, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.DATABRICKS_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      statement: query,
      warehouse_id: process.env.DATABRICKS_WAREHOUSE_ID,
      wait_timeout: "30s",
    }),
  });

  const data = await res.json();

  const columns = data?.manifest?.schema?.columns || [];
  const rows = data?.result?.data_array || [];

  return rows.map((row: any[]) => {
    const obj: any = {};
    columns.forEach((col: any, i: number) => {
      obj[col.name] = row[i];
    });
    return obj;
  });
}

export async function POST(req: NextRequest) {
  const { question } = await req.json();

  // ================= SQL ROUTE =================
  if (isAggregationQuery(question)) {
    try {
      console.log("SQL route:", question);

      const sql = await generateSQL(question);
      console.log("SQL:", sql);

      const result = await runSQL(sql);
      console.log("Result:", result);

      const summaryPrompt = `
You are a data analyst.

Summarize the SQL query result clearly and concisely.

Rules:
- Max 200-300 words
- Highlight key insights (totals, trends, top values)
- Use bullet points if helpful
- Do NOT mention SQL
- Do NOT mention JSON
- If no data, say "No meaningful data found"

User Question: ${question}

SQL Result:
${JSON.stringify(result)}
`;

      const summaryRes = await openai.chat.completions.create({
        model: "gpt-4o-mini",
        messages: [{ role: "user", content: summaryPrompt }],
      });

      const summary =
        summaryRes.choices[0].message.content || "No summary available";

      return new Response(summary, {
        headers: { "Content-Type": "text/plain" },
      });
    } catch (e: any) {
      return new Response(
        JSON.stringify({
          type: "error",
          message: e.message,
        }),
        {
          headers: { "Content-Type": "text/plain" },
        }
      );
    }
  }

  // ================= RAG ROUTE =================

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      try {
        let context: any;
        context = await vectorSearch(question);

        const rawAnswer = await callLLM([
          {
            role: "system",
            content:
              "Answer using context clearly. Answer only related to the context and tell user that you aren't supposed to give answers for generic questions",
          },
          {
            role: "user",
            content: `Q: ${question}\nContext: ${JSON.stringify(context)}`,
          },
        ]);

        const answer = formatAnswer(rawAnswer);

        for (const char of answer) {
          controller.enqueue(encoder.encode(char));
          await new Promise((r) => setTimeout(r, 5));
        }

        controller.close();
      } catch (e: any) {
        controller.enqueue(encoder.encode("Error: " + e.message));
        controller.close();
      }
    },
  });

  return new Response(stream);
}