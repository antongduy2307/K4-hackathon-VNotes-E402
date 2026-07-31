import type { SourceChunk } from "@/lib/api";

const EXPORT_API_BASE = process.env.NEXT_PUBLIC_EXPORT_API_URL ?? "http://localhost:8100";

// Một lượt hỏi-đáp thật trong chat, dùng làm input cho /notes/capture — cùng
// logic lọc (giữ rag_query, bỏ rag_summary/off-topic) mà agent loop dùng cho
// tool note_capture, chạy thuần Python không qua LLM.
export type ConversationTurn = {
  question: string;
  answer: string;
  tool_used: "rag_query" | "rag_summary" | null;
  sources: SourceChunk[];
};

export type CapturedNote = {
  question: string;
  answer: string;
  sources: SourceChunk[];
};

export type CaptureNotesResult = {
  doc_id: string;
  notes: CapturedNote[];
  kept_count: number;
  excluded_count: number;
};

async function parseJson<T>(res: Response, action: string): Promise<T> {
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(`${action} failed: ${res.status}${detail?.detail ? ` — ${detail.detail}` : ""}`);
  }
  return res.json();
}

export async function captureNotes(
  docId: string,
  conversationTurns: ConversationTurn[]
): Promise<CaptureNotesResult> {
  const res = await fetch(`${EXPORT_API_BASE}/notes/capture`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id: docId, conversation_turns: conversationTurns }),
  });
  return parseJson(res, "Capture notes");
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export async function exportAnki(docId: string, notes: CapturedNote[]): Promise<void> {
  const res = await fetch(`${EXPORT_API_BASE}/export/anki`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id: docId, notes }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(`Export Anki failed: ${res.status}${detail?.detail ? ` — ${detail.detail}` : ""}`);
  }
  downloadBlob(await res.blob(), `vlearn_${docId}.apkg`);
}

export async function exportObsidian(docId: string, notes: CapturedNote[], title?: string): Promise<void> {
  const res = await fetch(`${EXPORT_API_BASE}/export/obsidian`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id: docId, notes, title }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(`Export Obsidian failed: ${res.status}${detail?.detail ? ` — ${detail.detail}` : ""}`);
  }
  downloadBlob(await res.blob(), `vlearn_${docId}.md`);
}
