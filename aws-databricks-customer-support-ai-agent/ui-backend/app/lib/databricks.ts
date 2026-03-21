import axios from "axios";

const HOST = process.env.DATABRICKS_HOST!;
const TOKEN = process.env.DATABRICKS_TOKEN!;

export async function getEmbedding(text: string) {
  const res = await axios.post(
    "https://api.openai.com/v1/embeddings",
    {
      model: "text-embedding-3-large",
      input: text,
      dimensions: 1024
    },
    {
      headers: {
        Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
      },
    }
  );

  return res.data.data[0].embedding;
}

export async function vectorSearch(query: string) {
  const embedding = await getEmbedding(query);
  try {
  const res = await axios.post(
    `${HOST}/api/2.0/vector-search/indexes/customer_suppport_agent.raw.orders_index/query`,
    {
      query_text: query,         
      query_vector: embedding,  
      query_type: "HYBRID",  
      num_results: 10,
      columns: ['order_id','text']
    },
    {
      headers: {
        Authorization: `Bearer ${TOKEN}`,
        "Content-Type": "application/json",
      },
    }
  );
  return res.data;
} catch (err: any) {
  console.error("VECTOR ERROR FULL:", JSON.stringify(err.response?.data, null, 2));
  throw err;
}
}