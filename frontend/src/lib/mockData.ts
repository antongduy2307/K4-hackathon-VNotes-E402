import type {
  ChatMessage,
  ContentNode,
  CourseSource,
  ReviewStats,
  SavedFlashcard,
  SavedNote,
} from "./types";

// docId rỗng = trạng thái ban đầu, chưa upload gì — SlideViewer hiển thị màn
// hình "chưa có tài liệu" thay vì cố render PDF không tồn tại.
export const mockCourse: CourseSource = {
  docId: "",
  fileName: "",
};

export const mockContentTree: ContentNode[] = [
  { id: "transcript-d1", kind: "transcript", label: "Transcript bài giảng - Buổi 1" },
  { id: "slide-d1", kind: "slide", label: "Slide bài giảng - Buổi 1" },
];

export const mockReviewStats: ReviewStats = {
  today: 8,
  in3Days: 15,
  in7Days: 32,
};

export const mockNotes: SavedNote[] = [
  {
    id: "note-1",
    title: "Pipeline RAG cơ bản",
    snippet: "Ingest -> Chunk -> Embed -> Retrieve -> Generate...",
    createdAt: "2026-07-28",
  },
  {
    id: "note-2",
    title: "Chiến lược chunking",
    snippet: "Chia văn bản theo đoạn 500-800 token, overlap 15%...",
    createdAt: "2026-07-29",
  },
];

export const mockFlashcards: SavedFlashcard[] = [
  {
    id: "card-1",
    front: "RAG là gì?",
    back: "Retrieval-Augmented Generation - kết hợp truy xuất ngữ cảnh với sinh văn bản.",
    createdAt: "2026-07-28",
  },
  {
    id: "card-2",
    front: "Vector store dùng để làm gì?",
    back: "Lưu trữ embedding và hỗ trợ tìm kiếm tương đồng ngữ nghĩa.",
    createdAt: "2026-07-30",
  },
];

export const mockChatHistory: ChatMessage[] = [
  {
    id: "msg-1",
    role: "assistant",
    content:
      "Chào bạn! Mình là Trợ lý Học tập AI. Bạn có thể hỏi mình bất cứ điều gì về slide đang xem, mình sẽ trả lời dựa trên dữ liệu thật của khoá học.",
    createdAt: "09:00",
  },
];
