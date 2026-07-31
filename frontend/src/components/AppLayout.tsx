"use client";

import { useRef, useState } from "react";
import { Group, Panel } from "react-resizable-panels";
import { Header } from "@/components/Header";
import { LeftSidebar } from "@/components/LeftSidebar";
import { SlideViewer } from "@/components/SlideViewer";
import { RightChatbot } from "@/components/RightChatbot";
import { ResizeHandle } from "@/components/ResizeHandle";
import { askChat, fetchSummary, uploadSlide } from "@/lib/api";
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

function download(filename: string, content: string) {
  const blob = new Blob([content], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function AppLayout() {
  const [course, setCourse] = useState<CourseSource>(mockCourse);
  const [activeNodeId, setActiveNodeId] = useState(mockContentTree[1].id);
  const [currentPage, setCurrentPage] = useState(13);
  const [quickNote, setQuickNote] = useState("");
  const [notes, setNotes] = useState<SavedNote[]>(mockNotes);
  const [flashcards, setFlashcards] = useState<SavedFlashcard[]>(mockFlashcards);
  const [messages, setMessages] = useState<ChatMessage[]>(mockChatHistory);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const insight =
    "Case thật từ data: 12% học viên bỏ qua phần 'chiến lược chunking' và thường hỏi sai ở buổi ôn tập tiếp theo.";

  const currentSlide = course.pages.find((p) => p.page === currentPage) ?? course.pages[0];

  async function handleUploadDocument(file: File) {
    setIsUploading(true);
    try {
      const res = await uploadSlide(file);
      setCourse((prev) => ({ ...prev, docId: res.slide_id, fileName: file.name }));
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
      ? `Giải thích giúp mình đoạn này trong slide ${currentSlide.label}: "${selectedText}"`
      : `Bạn có thể tóm tắt nội dung chính của slide ${currentSlide.label} không?`;
    handleSendMessage(question);
  }

  async function handleSummarizeSlide() {
    setIsGenerating(true);
    try {
      const res = await fetchSummary(course.docId);
      setQuickNote(res.answer);
      pushAssistantMessage(`Tóm tắt slide ${currentSlide.label}: ${res.answer}`);
    } catch {
      const fallback = `${currentSlide.title}: ${currentSlide.bullets.join("; ")}`;
      setQuickNote(fallback);
      pushAssistantMessage(`Tóm tắt slide ${currentSlide.label}: ${fallback}`);
    } finally {
      setIsGenerating(false);
    }
  }

  function handleExtractFlashcard() {
    const card: SavedFlashcard = {
      id: crypto.randomUUID(),
      front: `${currentSlide.title}?`,
      back: currentSlide.bullets[0] ?? currentSlide.extractedText.slice(0, 80),
      createdAt: new Date().toISOString().slice(0, 10),
    };
    setFlashcards((prev) => [card, ...prev]);
    pushAssistantMessage(`Đã tạo flashcard mới từ ${currentSlide.label}.`);
  }

  function handleSaveQuickNote(value: string) {
    setQuickNote(value);
  }

  function handleSummarizeConversation() {
    const note: SavedNote = {
      id: crypto.randomUUID(),
      title: `Tóm tắt hội thoại - ${currentSlide.label}`,
      snippet: messages
        .slice(-3)
        .map((m) => m.content)
        .join(" | ")
        .slice(0, 120),
      createdAt: new Date().toISOString().slice(0, 10),
    };
    setNotes((prev) => [note, ...prev]);
    pushAssistantMessage("Đã tóm gọn kiến thức hội thoại và lưu vào Kho lưu trữ.");
  }

  return (
    <div className="flex flex-col h-screen w-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      <Header onOpenUpload={() => fileInputRef.current?.click()} />
      <input
        ref={fileInputRef}
        type="file"
        accept="application/pdf"
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
            fileName={course.fileName}
            totalLessons={mockContentTree.length}
            reviewStats={mockReviewStats}
            contentTree={mockContentTree}
            activeNodeId={activeNodeId}
            onSelectNode={setActiveNodeId}
            notes={notes}
            flashcards={flashcards}
            onExportNotes={() => download("notes.json", JSON.stringify(notes, null, 2))}
            onExportFlashcards={() =>
              download("flashcards.json", JSON.stringify(flashcards, null, 2))
            }
          />
        </Panel>

        <ResizeHandle />

        <Panel id="main-panel" minSize={360}>
          <SlideViewer
            course={course}
            currentPage={currentPage}
            onPageChange={setCurrentPage}
            quickNote={quickNote}
            onQuickNoteChange={handleSaveQuickNote}
            onSummarizeSlide={handleSummarizeSlide}
            onExtractFlashcard={handleExtractFlashcard}
            onAskAboutSlide={handleAskAboutSlide}
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
