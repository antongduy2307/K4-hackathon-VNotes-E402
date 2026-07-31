const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type IngestResponse = {
  doc_id: string;
  chunks_stored: number;
};

export type SummaryResponse = {
  doc_id: string;
  summary: string;
};

export type ChatSource = {
  page_start: number;
  page_end: number;
};

export type ChatResponse = {
  answer: string;
  sources: ChatSource[];
};

export async function uploadDocument(file: File): Promise<IngestResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/documents`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json();
}

export async function fetchSummary(docId: string): Promise<SummaryResponse> {
  const res = await fetch(`${API_BASE}/documents/${docId}/summary`);
  if (!res.ok) throw new Error(`Summary failed: ${res.status}`);
  return res.json();
}

export async function askChat(docId: string, question: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id: docId, question }),
  });
  if (!res.ok) throw new Error(`Chat failed: ${res.status}`);
  return res.json();
}
