const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_PREFIX = "/api/v1";

export type SlideStatus = "processing" | "ready" | "failed";

export type SlideResponse = {
  slide_id: string;
  title: string;
  original_filename: string;
  status: SlideStatus;
  chunk_count: number;
  created_at: string;
  error_message: string | null;
};

export type SlideUploadResponse = SlideResponse & { message: string };

export type SourceChunk = {
  chunk_id: string;
  page_number: number;
  chunk_index: number;
  text: string;
  score: number;
};

export type RagQueryResponse = {
  slide_id: string;
  answer: string;
  sources: SourceChunk[];
};

async function parseJson<T>(res: Response, action: string): Promise<T> {
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(`${action} failed: ${res.status}${detail?.detail ? ` — ${detail.detail}` : ""}`);
  }
  return res.json();
}

export async function uploadSlide(file: File, title?: string): Promise<SlideUploadResponse> {
  const form = new FormData();
  form.append("file", file);
  if (title) form.append("title", title);
  const res = await fetch(`${API_BASE}${API_PREFIX}/slides/upload`, {
    method: "POST",
    body: form,
  });
  return parseJson(res, "Upload");
}

export async function listSlides(): Promise<SlideResponse[]> {
  const res = await fetch(`${API_BASE}${API_PREFIX}/slides`);
  return parseJson(res, "List slides");
}

export async function getSlide(slideId: string): Promise<SlideResponse> {
  const res = await fetch(`${API_BASE}${API_PREFIX}/slides/${slideId}`);
  return parseJson(res, "Get slide");
}

export async function deleteSlide(slideId: string): Promise<{ slide_id: string; deleted: boolean }> {
  const res = await fetch(`${API_BASE}${API_PREFIX}/slides/${slideId}`, { method: "DELETE" });
  return parseJson(res, "Delete slide");
}

export async function fetchSummary(slideId: string): Promise<RagQueryResponse> {
  const res = await fetch(`${API_BASE}${API_PREFIX}/rag/summarize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ slide_id: slideId }),
  });
  return parseJson(res, "Summarize");
}

export async function askChat(slideId: string, question: string): Promise<RagQueryResponse> {
  const res = await fetch(`${API_BASE}${API_PREFIX}/rag/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ slide_id: slideId, question }),
  });
  return parseJson(res, "Chat");
}

// URL để render trực tiếp (vd <Document file={slideFileUrl(id)} /> của react-pdf) — không phải fetch JSON.
export function slideFileUrl(slideId: string): string {
  return `${API_BASE}${API_PREFIX}/slides/${slideId}/file`;
}

export type PageTextResponse = {
  slide_id: string;
  page_number: number;
  text: string;
};

export async function fetchPageText(slideId: string, pageNumber: number): Promise<PageTextResponse> {
  const res = await fetch(`${API_BASE}${API_PREFIX}/slides/${slideId}/pages/${pageNumber}`);
  return parseJson(res, "Get page text");
}
