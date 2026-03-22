import { NextRequest } from "next/server";
import { vectorSearch } from "@/lib/databricks";
import { callLLM } from "@/lib/llm";
import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY!,
});

// ================= ROUTER =================

async function shouldUseSQL(question: string) {
  const prompt = `
Classify the query.

Return ONLY one word:
SQL or RAG

Rules:
- SQL → aggregations, totals, trends, peak, highest, lowest
- RAG → explanations, descriptions, specific records

Query:
${question}
`;

  const res = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [{ role: "user", content: prompt }],
  });

  const decision = res.choices[0].message.content?.trim();
  return decision === "SQL";
}

// ================= SQL HELPERS =================

function cleanSQL(sql: string) {
  let cleaned = sql
    .replace(/```sql/g, "")
    .replace(/```/g, "")
    .replace(/^sql\s*/i, "")
    .trim();

  cleaned = cleaned.replace(
    /customer_support_agent\.raw\.orders/gi,
    "customer_suppport_agent.raw.orders"
  );

  return cleaned;
}

const today = new Date().toISOString().split("T")[0];

async function generateSQL(question: string) {
  const prompt = `
You are a SQL generator.

STRICT RULES:
- If the question has "Show me the numbers for this month/quarter/year/week or any date metrics" or "Show me product order history over past week" then use sql only not rag based. You are aware of today's date is ${today}. Always convert this ${today} to actual date filters suitable for Spark Sql and pass it to where condition.

- Dont answer any questions not in customer support, orders or payments domain.

- Use ONLY these exact tables:
  customer_suppport_agent.raw.orders and customer_suppport_agent.raw.user_activity_raw_intermediate
- Use ONLY columns from these tables. Do NOT make up any columns. Use joins also if needed.
- Use only where filters that correspond to distinct values from the columns not what you infer, for example event_type can only be CLICK,VIEW,PURCHASE. make them case insensitive though, so click, Click, CLICK are all valid.

- when you use where filters first look up distinct values from that filter column, use only those values.
- DO NOT change spelling
- DO NOT correct typos
- Always use full dataset for aggregations

Here is the schema for customer_suppport_agent.raw.orders:
  order_id
  customer_id
  product_id
  order_status
  order_amount
  currency
  payment_method
  payment_status
  shipping_address
  billing_address
  order_date
  delivery_date
  discount
  tax
  shipping_cost
  quantity
  seller_id
  warehouse_id
  region
  city
  pincode
  device_type
  browser
  ip_address
  is_gift
  gift_message
  coupon_code
  loyalty_points_used
  order_channel
  fulfillment_type
  delivery_partner
  status_timestamp
  created_at
  updated_at
  year
  month
  day

Here is the schema for customer_suppport_agent.raw.user_activity table:

  ad_id
  app_version
  browser
  campaign_id
  click_x
  click_y
  conversion
  created_at
  customer_id
  device_id
  device_type
  error_code
  error_message
  event_id
  event_type
  experiment_id
  feature_flag
  ip_address
  lat
  load_time
  location
  lon
  network
  os
  page_url
  referrer
  screen_resolution
  scroll_depth
  session_id
  time_on_page
  user_id

Return ONLY SQL.

Question: ${question}
`;

  const res = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [{ role: "user", content: prompt }],
  });

  return cleanSQL(res.choices[0].message.content!);
}

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

// ================= FOLLOW UPS =================

async function generateFollowUps(question: string, answer: string) {
  const prompt = `
Generate 3 short follow-up responses.

Rules:
- Max 10 words
- No numbering
- No symbols

For example if person asks what's the total revenue this month, next suggestion can be "Show me the revenue by products"

Dont answer or give followups for general questions, only for specific questions related to orders, customers, payments, products.

Question: ${question}
Answer: ${answer}
`;

  const res = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [{ role: "user", content: prompt }],
  });

  return (
    res.choices[0].message.content
      ?.split("\n")
      .map((q) => q.trim())
      .filter(Boolean)
      .slice(0, 3) || []
  );
}

// ================= MAIN =================

export async function POST(req: NextRequest) {
  const { question, history } = await req.json();

  const useSQL = await shouldUseSQL(question);
  console.log("ROUTE:", useSQL ? "SQL" : "RAG");

  // ================= SQL ROUTE =================
  if (useSQL) {
    try {
      const sql = await generateSQL(question);
      const result = await runSQL(sql);
      console.log(sql)
      console.log("Result", result)
      if (!result || result.length === 0) {
        const { context } = await vectorSearch(question);

        const ragAnswer = await callLLM([
          {
            role: "system",
            content: "Tell user that a full query of the database failed. Then answer using the context and give insights. Be concise.",
          },
          {
            role: "user",
            content: `Q: ${question}\n\nContext:\n${context}`,
          },
        ]);

        return new Response(
          JSON.stringify({
            answer: ragAnswer,
            table: [],
            followUps: [],
          }),
          { headers: { "Content-Type": "application/json" } }
        );
      }

      const summaryRes = await openai.chat.completions.create({
        model: "gpt-4o-mini",
        messages: [
          {
            role: "user",
            content: `
Answer and give insights.

Question: ${question}
Data: ${JSON.stringify(result)}
`,
          },
        ],
      });

      const summary =
        summaryRes.choices[0].message.content ||
        "No meaningful data found";

      const followUps = await generateFollowUps(question, summary);

      return new Response(
        JSON.stringify({
          answer: summary,
          table: result,
          followUps,
        }),
        { headers: { "Content-Type": "application/json" } }
      );
    } catch (e: any) {
      return new Response(
        JSON.stringify({ message: e.message }),
        { headers: { "Content-Type": "application/json" } }
      );
    }
  }

  // ================= RAG ROUTE =================

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      try {
        const { context } = await vectorSearch(question);

        const rawAnswer = await callLLM([
          {
            role: "system",
            content: `
You are a helpful assistant.
Use past conversation and context.
Be concise.
Dont answer and give followups for general questions, only for specific questions related to orders, customers, payments, products.
`,
          },
          ...(history || []).map((msg: any) => ({
            role: msg.role,
            content: msg.content,
          })),
          {
            role: "user",
            content: `Q: ${question}\n\nContext:\n${context}`,
          },
        ]);

        const followUps = await generateFollowUps(question, rawAnswer);

        for (const char of rawAnswer) {
          controller.enqueue(encoder.encode(char));
          await new Promise((r) => setTimeout(r, 5));
        }

        controller.enqueue(
          encoder.encode(
            "\n__FOLLOWUPS__" + JSON.stringify(followUps)
          )
        );

        controller.close();
      } catch (e: any) {
        controller.enqueue(encoder.encode("Error: " + e.message));
        controller.close();
      }
    },
  });

  return new Response(stream);
}
