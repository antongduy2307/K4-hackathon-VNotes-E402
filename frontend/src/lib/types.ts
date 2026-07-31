export type ReviewStats = {
  today: number;
  in3Days: number;
  in7Days: number;
};

export type SlidePage = {
  page: number;
  label: string;
  title: string;
  bullets: string[];
  extractedText: string;
};

export type CourseSource = {
  docId: string;
  fileName: string;
  totalPages: number;
  pages: SlidePage[];
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
