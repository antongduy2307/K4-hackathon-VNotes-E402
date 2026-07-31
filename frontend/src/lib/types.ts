export type ReviewStats = {
  today: number;
  in3Days: number;
  in7Days: number;
};

// Nội dung từng trang lấy trực tiếp từ backend (PDF render qua react-pdf +
// text trích xuất qua GET /slides/{id}/pages/{n}) — không còn state tĩnh ở
// đây, xem SlideViewer.tsx.
export type CourseSource = {
  docId: string;
  fileName: string;
};

export type ContentNode = {
  id: string;
  kind: "transcript" | "slide";
  label: string;
};

export type SavedNote = {
  id: string;
  title: string;
  snippet: string;
  createdAt: string;
};

export type SavedFlashcard = {
  id: string;
  front: string;
  back: string;
  createdAt: string;
};

export type ChatRole = "user" | "assistant";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: string;
};

export type AgentStatus = {
  mode: string;
  model: string;
  online: boolean;
};
