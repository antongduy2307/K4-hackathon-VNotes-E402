"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  BookOpenCheck,
  ChevronLeft,
  ChevronRight,
  Layers,
  MessageCircleQuestion,
  Sparkles,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { FlashcardFlip } from "@/components/FlashcardFlip";
import type { CourseSource } from "@/lib/types";

type SlideViewerProps = {
  course: CourseSource;
  currentPage: number;
  onPageChange: (page: number) => void;
  quickNote: string;
  onQuickNoteChange: (value: string) => void;
  onSummarizeSlide: () => void;
  onExtractFlashcard: () => void;
  onAskAboutSlide: (selectedText?: string) => void;
  isGenerating?: boolean;
};

export function SlideViewer({
  course,
  currentPage,
  onPageChange,
  quickNote,
  onQuickNoteChange,
  onSummarizeSlide,
  onExtractFlashcard,
  onAskAboutSlide,
  isGenerating,
}: SlideViewerProps) {
  const [zoom, setZoom] = useState(100);
  const [showExtractedText, setShowExtractedText] = useState(true);
  const [selectedText, setSelectedText] = useState("");
  // Trạng thái riêng cho hiệu ứng thẻ Flashcard 3D: đang tạo hay đã sẵn sàng
  const [flashcardState, setFlashcardState] = useState<"idle" | "generating" | "ready">("idle");

  const slide = useMemo(
    () => course.pages.find((p) => p.page === currentPage) ?? course.pages[0],
    [course.pages, currentPage]
  );

  // Dấu thời gian của lần chuyển trang gần nhất, dùng để debounce/throttle thao tác lăn chuột
  const lastWheelNavRef = useRef(0);
  const WHEEL_NAV_COOLDOWN_MS = 550;
  const WHEEL_NAV_THRESHOLD = 12;

  // Lăn chuột trong khung Slide sẽ chuyển sang trang kế tiếp/trước đó (kiểu Snapping Page),
  // đồng thời vẫn giữ nguyên các nút điều khiển Prev/Next/Zoom truyền thống bên trên.
  function handleSlideWheel(e: React.WheelEvent<HTMLDivElement>) {
    if (Math.abs(e.deltaY) < WHEEL_NAV_THRESHOLD) return;

    const now = Date.now();
    if (now - lastWheelNavRef.current < WHEEL_NAV_COOLDOWN_MS) return;
    lastWheelNavRef.current = now;

    if (e.deltaY > 0) {
      onPageChange(Math.min(course.totalPages, currentPage + 1));
    } else {
      onPageChange(Math.max(1, currentPage - 1));
    }
  }

  function handleExtractFlashcardClick() {
    setFlashcardState("generating");
    // Cho hiệu ứng xoay lật chạy một nhịp trước khi trả kết quả, mô phỏng quá trình AI "suy nghĩ"
    setTimeout(() => {
      onExtractFlashcard();
      setFlashcardState("ready");
    }, 1400);
  }

  const flashcardFront = `${slide.title}?`;
  const flashcardBack = slide.bullets[0] ?? slide.extractedText.slice(0, 100);

  return (
    <div className="w-full h-full flex flex-col min-h-0 bg-slate-50/50 dark:bg-slate-950">
      {/* Thanh điều hướng trang trên cùng */}
      <div className="h-12 flex items-center justify-between px-4 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 gap-3">
        <div className="flex items-center gap-2 shrink-0">
          <motion.button
            whileHover={{ scale: 1.06 }}
            whileTap={{ scale: 0.92 }}
            onClick={() => onPageChange(Math.max(1, currentPage - 1))}
            disabled={currentPage <= 1}
            className="w-7 h-7 rounded-lg border border-slate-200 dark:border-slate-700 disabled:opacity-30 hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center justify-center text-slate-600 dark:text-slate-300"
          >
            <ChevronLeft className="w-4 h-4" />
          </motion.button>
          <span className="text-xs text-slate-500 dark:text-slate-400 w-14 text-center tabular-nums">
            {currentPage}/{course.totalPages}
          </span>
          <motion.button
            whileHover={{ scale: 1.06 }}
            whileTap={{ scale: 0.92 }}
            onClick={() => onPageChange(Math.min(course.totalPages, currentPage + 1))}
            disabled={currentPage >= course.totalPages}
            className="w-7 h-7 rounded-lg border border-slate-200 dark:border-slate-700 disabled:opacity-30 hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center justify-center text-slate-600 dark:text-slate-300"
          >
            <ChevronRight className="w-4 h-4" />
          </motion.button>
        </div>

        <div className="flex-1 flex items-center gap-1 overflow-x-auto min-w-0">
          {course.pages.map((p) => (
            <motion.button
              key={p.page}
              whileHover={{ scale: 1.12 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => onPageChange(p.page)}
              title={p.label}
              className={cn(
                "shrink-0 text-[11px] w-6 h-6 rounded-md flex items-center justify-center transition-colors",
                p.page === currentPage
                  ? "bg-indigo-600 text-white font-semibold"
                  : "text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              )}
            >
              {p.page}
            </motion.button>
          ))}
        </div>

        <div className="flex items-center gap-1 shrink-0">
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.88 }}
            onClick={() => setZoom((z) => Math.max(50, z - 10))}
            className="w-7 h-7 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center justify-center text-slate-600 dark:text-slate-300"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </motion.button>
          <span className="text-[11px] text-slate-400 w-9 text-center tabular-nums">{zoom}%</span>
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.88 }}
            onClick={() => setZoom((z) => Math.min(200, z + 10))}
            className="w-7 h-7 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center justify-center text-slate-600 dark:text-slate-300"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </motion.button>
        </div>

        <span className="text-xs px-2 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-300 font-medium shrink-0">
          [{slide.label}]
        </span>
      </div>

      {/* Thanh hành động nhanh */}
      <div className="flex gap-2 px-4 py-2 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.96 }}
          onClick={onSummarizeSlide}
          disabled={isGenerating}
          className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-indigo-200 dark:border-indigo-800 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-950 disabled:opacity-50"
        >
          <BookOpenCheck className="w-3.5 h-3.5" /> Tóm tắt Slide này
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.96 }}
          onClick={handleExtractFlashcardClick}
          disabled={isGenerating || flashcardState === "generating"}
          className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-violet-200 dark:border-violet-800 bg-violet-50 dark:bg-violet-950/40 text-violet-700 dark:text-violet-300 hover:bg-violet-100 dark:hover:bg-violet-950 disabled:opacity-50"
        >
          <Layers className="w-3.5 h-3.5" /> Trích xuất Flashcard
        </motion.button>
      </div>

      {/* Khung nội dung có thể cuộn */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* pageKey đổi mỗi khi sang trang -> remount PageTransition -> tự phát lại hiệu ứng Skeleton + chuyển trang */}
        <PageTransition pageKey={slide.page}>
          <div
            onWheel={handleSlideWheel}
            title="Lăn chuột để chuyển trang"
            className="max-w-3xl mx-auto origin-top rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm hover:shadow-md transition-shadow p-8 min-h-[300px]"
            style={{ transform: `scale(${zoom / 100})` }}
          >
            <p className="text-xs text-indigo-500 dark:text-indigo-400 font-medium mb-2">
              [{slide.label}]
            </p>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
              {slide.title}
            </h2>
            <ul className="mt-4 space-y-2.5">
              {slide.bullets.map((b, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-300"
                >
                  <span className="mt-1.5 w-1.5 h-1.5 shrink-0 rounded-full bg-indigo-500" />
                  {b}
                </li>
              ))}
            </ul>
          </div>
        </PageTransition>

        {/* Khay xem text đã trích xuất */}
        <details
          open={showExtractedText}
          onToggle={(e) => setShowExtractedText(e.currentTarget.open)}
          className="max-w-3xl mx-auto mt-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800"
        >
          <summary className="cursor-pointer text-xs text-slate-500 dark:text-slate-400 px-4 py-2 select-none">
            Xem text đã trích xuất (để bôi đen hỏi AI)
          </summary>
          <div className="px-4 pb-4">
            <p
              onMouseUp={() => {
                const sel = window.getSelection()?.toString().trim();
                setSelectedText(sel && sel.length > 0 ? sel : "");
              }}
              className="select-text whitespace-pre-wrap text-[13px] text-slate-600 dark:text-slate-300 leading-relaxed"
            >
              {slide.extractedText}
            </p>
            <AnimatePresence>
              {selectedText && (
                <motion.div
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  className="mt-2 flex items-center justify-between rounded-lg bg-indigo-50 dark:bg-indigo-950/40 px-3 py-2 text-xs text-indigo-700 dark:text-indigo-300"
                >
                  <span className="truncate">Đã chọn: &ldquo;{selectedText}&rdquo;</span>
                  <button
                    onClick={() => onAskAboutSlide(selectedText)}
                    className="ml-2 shrink-0 font-semibold underline"
                  >
                    Hỏi AI
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </details>

        {/* Nhóm hành động phụ */}
        <div className="max-w-3xl mx-auto mt-3 flex flex-wrap gap-2">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.96 }}
            onClick={() => onAskAboutSlide()}
            className="flex items-center gap-1.5 text-sm font-medium px-3 py-2 rounded-lg border border-indigo-200 dark:border-indigo-800 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-950"
          >
            <MessageCircleQuestion className="w-4 h-4" /> Hỏi về Slide này ([{slide.label}])
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.96 }}
            onClick={handleExtractFlashcardClick}
            disabled={flashcardState === "generating"}
            className="flex items-center gap-1.5 text-sm font-medium px-3 py-2 rounded-lg border border-violet-200 dark:border-violet-800 bg-violet-50 dark:bg-violet-950/40 text-violet-700 dark:text-violet-300 hover:bg-violet-100 dark:hover:bg-violet-950 disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4" /> Tạo Flashcard từ trang này
          </motion.button>
        </div>

        {/* Khung ghi chú nhanh */}
        <div className="max-w-3xl mx-auto mt-4 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-2">
            Ghi chú nhanh
          </h3>
          <textarea
            value={quickNote}
            onChange={(e) => onQuickNoteChange(e.target.value)}
            rows={4}
            placeholder="Ghi chú được trích xuất từ AI sẽ tự động thêm vào đây, bạn có thể chỉnh sửa trực tiếp..."
            className="w-full text-sm text-slate-700 dark:text-slate-200 dark:bg-slate-800 leading-relaxed outline-none resize-none border border-slate-100 dark:border-slate-700 rounded-lg p-3 focus:ring-2 focus:ring-indigo-200 dark:focus:ring-indigo-800 transition-shadow"
          />
        </div>
      </div>

      {/* Overlay thẻ Flashcard xoay lật 3D khi đang trích xuất / khi xem kết quả */}
      {flashcardState !== "idle" && (
        <FlashcardFlip
          front={flashcardFront}
          back={flashcardBack}
          status={flashcardState === "generating" ? "generating" : "ready"}
          onClose={() => setFlashcardState("idle")}
        />
      )}
    </div>
  );
}

// Bọc nội dung trang trong một khoảng Skeleton ngắn rồi chuyển cảnh mượt sang nội dung thật.
// Dùng "key" để ép remount mỗi khi sang trang mới, nhờ đó trạng thái loading luôn khởi tạo lại
// mà không cần gọi setState trực tiếp trong effect (tránh cascading render).
function PageTransition({ pageKey, children }: { pageKey: number; children: React.ReactNode }) {
  return (
    <AnimatePresence mode="wait">
      <PageTransitionFrame key={pageKey}>{children}</PageTransitionFrame>
    </AnimatePresence>
  );
}

function PageTransitionFrame({ children }: { children: React.ReactNode }) {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 260);
    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="max-w-3xl mx-auto rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm p-8 min-h-[300px] space-y-4"
      >
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-6 w-2/3" />
        <div className="space-y-2.5 pt-2">
          <Skeleton className="h-3.5 w-full" />
          <Skeleton className="h-3.5 w-5/6" />
          <Skeleton className="h-3.5 w-3/4" />
        </div>
      </motion.div>
    );
  }

  return (
    // Hiệu ứng chuyển trang mượt như lật slide thật: trang mới trượt vào + mờ dần
    <motion.div
      initial={{ opacity: 0, x: 24 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -24 }}
      transition={{ duration: 0.28, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  );
}
