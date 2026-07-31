import type {
  ChatMessage,
  ContentNode,
  CourseSource,
  ReviewStats,
  SavedFlashcard,
  SavedNote,
  SlidePage,
} from "./types";

function buildPages(total: number): SlidePage[] {
  return Array.from({ length: total }, (_, i) => {
    const page = i + 1;
    return {
      page,
      label: `D1-p${page}`,
      title: `Slide ${page}: Kiến trúc hệ thống RAG`,
      bullets: [
        "Tổng quan pipeline: Ingest -> Chunk -> Embed -> Retrieve -> Generate",
        "Vai trò của vector store trong truy xuất ngữ cảnh",
        "Chiến lược đánh giá chất lượng câu trả lời",
      ],
      extractedText:
        "Đây là nội dung văn bản được trích xuất từ slide bài giảng, học viên có thể bôi đen đoạn text này để hỏi AI trực tiếp về chi tiết liên quan tới kiến trúc RAG, cách chunking văn bản và cách đánh giá độ chính xác của hệ thống.",
    };
  });
}

export const mockCourse: CourseSource = {
  docId: "demo-doc-001",
  fileName: "AI-Slide-Tutor-BaiGiang-D1.pdf",
  totalPages: 29,
  pages: buildPages(29),
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
