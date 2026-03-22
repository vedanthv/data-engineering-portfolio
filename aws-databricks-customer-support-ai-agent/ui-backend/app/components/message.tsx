"use client";

export default function Message({ content, role }: any) {
  let parsed: any = null;
  let cleanContent = content;

  if (typeof content === "string" && content.includes("__FOLLOWUPS__")) {
    const [main] = content.split("__FOLLOWUPS__");
    cleanContent = main.trim();

    try {
      parsed = JSON.parse(main);
    } catch {
      parsed = null;
    }
  } else {
    try {
      parsed = JSON.parse(content);
    } catch {
      parsed = null;
    }
  }

  return (
    <div className={`flex gap-3 ${role === "user" ? "justify-end" : ""}`}>
      {/* Assistant Avatar */}
      {role === "assistant" && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-center text-sm font-bold">
          AI
        </div>
      )}

      {/* Message Bubble */}
      <div
        className={`max-w-3xl px-4 py-3 rounded-2xl shadow-lg ${
          role === "user"
            ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white"
            : "bg-white/10 backdrop-blur-md text-white border border-white/10"
        }`}
      >
        {parsed?.table ? (
          <>
            <FormattedText text={parsed.answer} />
            <div className="mt-4">
              <Table data={parsed.table} />
            </div>
          </>
        ) : parsed?.type === "table" ? (
          <Table data={parsed.data} />
        ) : (
          <FormattedText text={cleanContent} />
        )}
      </div>

      {/* User Avatar */}
      {role === "user" && (
        <div className="w-8 h-8 rounded-full bg-white text-black flex items-center justify-center text-sm font-bold">
          U
        </div>
      )}
    </div>
  );
}

// ================= TABLE =================

function Table({ data }: any) {
  if (!data?.length) return <p>No data</p>;

  const cols = Object.keys(data[0]);

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm border border-white/10 rounded-lg overflow-hidden">
        <thead className="bg-white/10">
          <tr>
            {cols.map((c) => (
              <th key={c} className="px-3 py-2 text-left">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row: any, i: number) => (
            <tr key={i} className="hover:bg-white/5 transition">
              {cols.map((c) => (
                <td key={c} className="px-3 py-2">
                  {row[c]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ================= TEXT =================

function FormattedText({ text }: any) {
  return (
    <div className="whitespace-pre-wrap space-y-2 leading-relaxed">
      {text.split("\n").map((line: string, i: number) => {
        const trimmed = line.trim();

        if (trimmed.startsWith("### ")) {
          return (
            <div key={i} className="text-lg font-semibold text-indigo-300 mt-2">
              {trimmed.replace("### ", "")}
            </div>
          );
        }

        if (trimmed.startsWith("## ")) {
          return (
            <div key={i} className="text-xl font-semibold text-indigo-200 mt-3">
              {trimmed.replace("## ", "")}
            </div>
          );
        }

        if (trimmed.startsWith("# ")) {
          return (
            <div key={i} className="text-2xl font-bold text-white mt-4">
              {trimmed.replace("# ", "")}
            </div>
          );
        }

        if (trimmed.startsWith("- ")) {
          return (
            <div key={i} className="flex gap-2">
              <span>•</span>
              <span>{formatInline(trimmed.slice(2))}</span>
            </div>
          );
        }

        return <div key={i}>{formatInline(line)}</div>;
      })}
    </div>
  );
}

function formatInline(text: string) {
  const parts = text.split(/(\*\*.*?\*\*)/g);

  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <span key={i} className="font-semibold text-indigo-300">
          {part.slice(2, -2)}
        </span>
      );
    }
    return <span key={i}>{part}</span>;
  });
}
