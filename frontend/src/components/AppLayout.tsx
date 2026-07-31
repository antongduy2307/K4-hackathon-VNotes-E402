"use client";

import { useRef, useState } from "react";
import { Group, Panel } from "react-resizable-panels";
import { Header } from "@/components/Header";
import { LeftSidebar } from "@/components/LeftSidebar";
import { SlideViewer } from "@/components/SlideViewer";
import { RightChatbot } from "@/components/RightChatbot";
import { ResizeHandle } from "@/components/ResizeHandle";
import { askChat, fetchSummary, uploadSlide } from "@/lib/api";
import { captureNotes, exportAnki, exportObsidian, type ConversationTurn } from "@/lib/exportApi";
import {
  mockChatHistory,
  mockContentTree,
  mockCourse,
  mockFlashcards,
  mockNotes,
  mockReviewStats,
} from "@/lib/mockData";
import type { ChatMessage, CourseSource, SavedFlashcard, SavedNote } from "@/lib/types";

function nowLabel() {
  return new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
}

export function AppLayout() {
  const [course, setCourse] = useState<CourseSource>(mockCourse);
  const [activeNodeId, setActiveNodeId] = useState(mockContentTree[1].id);
  const [currentPage, setCurrentPage] = useState(1);
  const [currentPageText, setCurrentPageText] = useState("");
  const [quickNote, setQuickNote] = useState("");
  const [notes, setNotes] = useState<SavedNote[]>(mockNotes);
  const [flashcards, setFlashcards] = useState<SavedFlashcard[]>(mockFlashcards);
  const [messages, setMessages] = useState<ChatMessage[]>(mockChatHistory);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  // Lịch sử hỏi-đáp thật, dùng làm nguồn cho export Anki/Obsidian (note_capture
  // lọc bỏ tool_used=rag_summary và câu hỏi off-topic khi build ghi chú thật).
  const [conversationTurns, setConversationTurns] = useState<ConversationTurn[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const insight =
    "Case thật từ data: 12% học viên bỏ qua phần 'chiến lược chunking' và thường hỏi sai ở buổi ôn tập tiếp theo.";

  async function handleUploadDocument(file: File) {
    setIsUploading(true);
    try {
      const res = await uploadSlide(file);
      setCourse({ docId: res.slide_id, fileName: file.name });
      setCurrentPage(1);
      pushAssistantMessage(
        `Đã nhập tài liệu "${file.name}" thành công (${res.chunk_count} đoạn nội dung). Bạn có thể bắt đầu hỏi mình về nội dung này.`
      );
    } catch {
      pushAssistantMessage("Không thể nhập tài liệu lúc này. Vui lòng thử lại sau.");
    } finally {
      setIsUploading(false);
    }
  }

  function pushAssistantMessage(content: string) {
    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: "assistant", content, createdAt: nowLabel() },
    ]);
  }

  async function handleSendMessage(text: string) {
    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: "user", content: text, createdAt: nowLabel() },
    ]);
    setIsGenerating(true);
    try {
      const res = await askChat(course.docId, text);
      pushAssistantMessage(res.answer);
      setConversationTurns((prev) => [
        ...prev,
        { question: text, answer: res.answer, tool_used: "rag_query", sources: res.sources },
      ]);
    } catch {
      pushAssistantMessage(
        "Mình chưa thể kết nối tới RAG backend. Hãy chắc chắn đã nhập tài liệu và backend đang chạy."
      );
    } finally {
      setIsGenerating(false);
    }
  }

  function handleAskAboutSlide(selectedText?: string) {
    const question = selectedText
      ? `Giải thích giúp mình đoạn này ở trang ${currentPage}: "${selectedText}"`
      : `Bạn có thể tóm tắt nội dung chính của trang ${currentPage} không?`;
    handleSendMessage(question);
  }

  async function handleSummarizeSlide() {
    setIsGenerating(true);
    try {
      const res = await fetchSummary(course.docId);
      setQuickNote(res.answer);
      pushAssistantMessage(`Tóm tắt tài liệu (trang ${currentPage} đang xem): ${res.answer}`);
      setConversationTurns((prev) => [
        ...prev,
        { question: `Tóm tắt tài liệu (trang ${currentPage})`, answer: res.answer, tool_used: "rag_summary", sources: res.sources },
      ]);
    } catch {
      pushAssistantMessage("Không tóm tắt được lúc này. Hãy chắc chắn đã nhập tài liệu và backend đang chạy.");
    } finally {
      setIsGenerating(false);
    }
  }

  function handleExtractFlashcard() {
    const card: SavedFlashcard = {
      id: crypto.randomUUID(),
      front: `Trang ${currentPage} — ${course.fileName}?`,
      back: currentPageText.slice(0, 160) || "(chưa có nội dung trích xuất cho trang này)",
      createdAt: new Date().toISOString().slice(0, 10),
    };
    setFlashcards((prev) => [card, ...prev]);
    pushAssistantMessage(`Đã tạo flashcard mới từ trang ${currentPage}.`);
  }

  function handleSaveQuickNote(value: string) {
    setQuickNote(value);
  }

  async function handleSummarizeConversation() {
    if (conversationTurns.length === 0) {
      pushAssistantMessage("Chưa có hội thoại hỏi-đáp nào để tóm gọn — hãy hỏi mình về nội dung tài liệu trước.");
      return;
    }
    try {
      const result = await captureNotes(course.docId, conversationTurns);
      if (result.kept_count === 0) {
        pushAssistantMessage("Không có câu hỏi nào đủ điều kiện để lưu thành ghi chú (đã lọc bỏ câu hỏi tóm tắt/off-topic).");
        return;
      }
      const savedNotes: SavedNote[] = result.notes.map((n) => ({
        id: crypto.randomUUID(),
        title: n.question.slice(0, 60),
        snippet: n.answer.slice(0, 120),
        createdAt: new Date().toISOString().slice(0, 10),
      }));
      setNotes((prev) => [...savedNotes, ...prev]);
      pushAssistantMessage(`Đã tóm gọn ${result.kept_count} ghi chú và lưu vào Kho lưu trữ.`);
    } catch {
      pushAssistantMessage("Không kết nối được tới dịch vụ export. Hãy chắc chắn export_api đang chạy (port 8100).");
    }
  }

  async function handleExportAnki() {
    if (conversationTurns.length === 0) {
      pushAssistantMessage("Chưa có hội thoại nào để xuất Anki — hãy hỏi mình về nội dung tài liệu trước.");
      return;
    }
    setIsExporting(true);
    try {
      const captured = await captureNotes(course.docId, conversationTurns);
      if (captured.kept_count === 0) {
        pushAssistantMessage("Không có ghi chú nào đủ điều kiện để xuất Anki.");
        return;
      }
      await exportAnki(course.docId, captured.notes);
      pushAssistantMessage(`Đã xuất ${captured.kept_count} thẻ Anki (.apkg).`);
    } catch {
      pushAssistantMessage("Xuất Anki thất bại. Hãy chắc chắn export_api đang chạy (port 8100).");
    } finally {
      setIsExporting(false);
    }
  }

  async function handleExportObsidian() {
    if (conversationTurns.length === 0) {
      pushAssistantMessage("Chưa có hội thoại nào để xuất Obsidian — hãy hỏi mình về nội dung tài liệu trước.");
      return;
    }
    setIsExporting(true);
    try {
      const captured = await captureNotes(course.docId, conversationTurns);
      if (captured.kept_count === 0) {
        pushAssistantMessage("Không có ghi chú nào đủ điều kiện để xuất Obsidian.");
        return;
      }
      await exportObsidian(course.docId, captured.notes, course.fileName);
      pushAssistantMessage(`Đã xuất ${captured.kept_count} ghi chú sang Obsidian (.md).`);
    } catch {
      pushAssistantMessage("Xuất Obsidian thất bại. Hãy chắc chắn export_api đang chạy (port 8100).");
    } finally {
      setIsExporting(false);
    }
  }

  return (
    <div className="flex flex-col h-screen w-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      <Header onOpenUpload={() => fileInputRef.current?.click()} />
      <input
        ref={fileInputRef}
        type="file"
        accept="application/pdf,.pptx"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleUploadDocument(file);
          e.target.value = "";
        }}
      />

      {/* Khung 3 cột co giãn: kéo thanh phân cách để đổi chiều rộng cột trái/phải,
          cột giữa (SlideViewer) tự động lấp đầy phần không gian còn lại. */}
      <Group orientation="horizontal" className="flex-1 min-h-0">
        <Panel
          id="left-panel"
          defaultSize={320}
          minSize={200}
          maxSize={450}
          collapsible
          className="border-r border-slate-200 dark:border-slate-800"
        >
          <LeftSidebar
            fileName={course.fileName || "Chưa có tài liệu"}
            totalLessons={mockContentTree.length}
            reviewStats={mockReviewStats}
            contentTree={mockContentTree}
            activeNodeId={activeNodeId}
            onSelectNode={setActiveNodeId}
            notes={notes}
            flashcards={flashcards}
            onExportAnki={handleExportAnki}
            onExportObsidian={handleExportObsidian}
            isExporting={isExporting}
          />
        </Panel>

        <ResizeHandle />

        <Panel id="main-panel" minSize={360}>
          <SlideViewer
            docId={course.docId}
            fileName={course.fileName}
            currentPage={currentPage}
            onPageChange={setCurrentPage}
            quickNote={quickNote}
            onQuickNoteChange={handleSaveQuickNote}
            onSummarizeSlide={handleSummarizeSlide}
            onExtractFlashcard={handleExtractFlashcard}
            onAskAboutSlide={handleAskAboutSlide}
            onPageTextChange={setCurrentPageText}
            isGenerating={isGenerating || isUploading}
          />
        </Panel>

        <ResizeHandle />

        <Panel
          id="right-panel"
          defaultSize={384}
          minSize={300}
          maxSize={600}
          collapsible
          className="border-l border-slate-200 dark:border-slate-800"
        >
          <RightChatbot
            agentStatus={{ mode: "RAG thật", model: "gpt-4o-mini", online: true }}
            messages={messages}
            onSendMessage={handleSendMessage}
            isGenerating={isGenerating}
            onSummarizeConversation={handleSummarizeConversation}
            insight={insight}
          />
        </Panel>
      </Group>
    </div>
  );
}
