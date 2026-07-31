"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { AnimatePresence, motion } from "framer-motion";
import {
  BookOpenCheck,
  ChevronLeft,
  ChevronRight,
  FileWarning,
  Layers,
  MessageCircleQuestion,
  Sparkles,
  UploadCloud,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { FlashcardFlip } from "@/components/FlashcardFlip";
import { fetchPageText, slideFileUrl } from "@/lib/api";

// react-pdf/pdfjs-dist reference browser-only globals at import time, which
// crashes Next.js's server-side prerender — load it client-only.
const PdfPage = dynamic(() => import("@/components/PdfPage"), {
  ssr: false,
  loading: () => <Skeleton className="w-[600px] h-[420px]" />,
});

type SlideViewerProps = {
  docId: string;
  fileName: string;
  currentPage: number;
  onPageChange: (page: number) => void;
  quickNote: string;
  onQuickNoteChange: (value: string) => void;
  onSummarizeSlide: () => void;
  onExtractFlashcard: () => void;
  onAskAboutSlide: (selectedText?: string) => void;
  onPageTextChange: (text: string) => void;
  isGenerating?: boolean;
};

function isPptx(fileName: string): boolean {
  return fileName.toLowerCase().endsWith(".pptx");
}

export function SlideViewer({
  docId,
  fileName,
  currentPage,
  onPageChange,
  quickNote,
  onQuickNoteChange,
  onSummarizeSlide,
  onExtractFlashcard,
  onAskAboutSlide,
  onPageTextChange,
  isGenerating,
}: SlideViewerProps) {
  const [zoom, setZoom] = useState(100);
  const [numPages, setNumPages] = useState(0);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [pageText, setPageText] = useState("");
  const [pageTextLoading, setPageTextLoading] = useState(false);
  const [showExtractedText, setShowExtractedText] = useState(true);
  const [selectedText, setSelectedText] = useState("");
  const [flashcardState, setFlashcardState] = useState<"idle" | "generating" | "ready">("idle");

  const hasDoc = docId.length > 0;
  const pptx = isPptx(fileName);
  const fileUrl = useMemo(() => (hasDoc ? slideFileUrl(docId) : undefined), [hasDoc, docId]);

  const lastWheelNavRef = useRef(0);
  const WHEEL_NAV_COOLDOWN_MS = 550;
  const WHEEL_NAV_THRESHOLD = 12;

  function handleSlideWheel(e: React.WheelEvent<HTMLDivElement>) {
    if (Math.abs(e.deltaY) < WHEEL_NAV_THRESHOLD || numPages === 0) return;
    const now = Date.now();
    if (now - lastWheelNavRef.current < WHEEL_NAV_COOLDOWN_MS) return;
    lastWheelNavRef.current = now;
    if (e.deltaY > 0) {
      onPageChange(Math.min(numPages, currentPage + 1));
    } else {
      onPageChange(Math.max(1, currentPage - 1));
    }
  }

  function handleExtractFlashcardClick() {
    setFlashcardState("generating");
    setTimeout(() => {
      onExtractFlashcard();
      setFlashcardState("ready");
    }, 1400);
  }

  // Tải lại text đã trích xuất thật của đúng trang đang xem mỗi khi đổi tài liệu/trang.
  useEffect(() => {
    if (!hasDoc || pptx) {
      setPageText("");
      onPageTextChange("");
      return;
    }
    let cancelled = false;
    setPageTextLoading(true);
    fetchPageText(docId, currentPage)
      .then((res) => {
        if (cancelled) return;
        setPageText(res.text);
        onPageTextChange(res.text);
      })
      .catch(() => {
        if (cancelled) return;
        setPageText("");
        onPageTextChange("");
      })
      .finally(() => {
        if (!cancelled) setPageTextLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [docId, currentPage, hasDoc, pptx]);

  const flashcardFront = `Trang ${currentPage} — ${fileName || "tài liệu"}?`;
  const flashcardBack = pageText.slice(0, 160) || "(chưa có nội dung trích xuất cho trang này)";

  if (!hasDoc) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center gap-3 bg-slate-50/50 dark:bg-slate-950 text-center px-6">
        <UploadCloud className="w-10 h-10 text-slate-300 dark:text-slate-700" />
        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
          Chưa có tài liệu nào được nhập
        </p>
        <p className="text-xs text-slate-400 max-w-xs">
          Bấm &quot;Nhập PDF/Slide&quot; ở góc trên bên phải để bắt đầu.
        </p>
      </div>
    );
  }

  if (pptx) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center gap-3 bg-slate-50/50 dark:bg-slate-950 text-center px-6">
        <FileWarning className="w-10 h-10 text-amber-400" />
        <p className="text-sm font-medium text-slate-600 dark:text-slate-300">
          Chưa hỗ trợ xem trực tiếp file .pptx
        </p>
        <p className="text-xs text-slate-400 max-w-sm">
          Tài liệu &quot;{fileName}&quot; đã được đưa vào RAG và có thể hỏi/tóm tắt bình
          thường qua khung chat bên phải — chỉ riêng phần xem trực quan từng trang
          slide chưa hỗ trợ cho .pptx (cần chuyển đổi sang PDF trước).
        </p>
      </div>
    );
  }

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
            {currentPage}/{numPages || "…"}
          </span>
          <motion.button
            whileHover={{ scale: 1.06 }}
            whileTap={{ scale: 0.92 }}
            onClick={() => onPageChange(Math.min(numPages || currentPage, currentPage + 1))}
            disabled={numPages === 0 || currentPage >= numPages}
            className="w-7 h-7 rounded-lg border border-slate-200 dark:border-slate-700 disabled:opacity-30 hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center justify-center text-slate-600 dark:text-slate-300"
          >
            <ChevronRight className="w-4 h-4" />
          </motion.button>
        </div>

        <div className="flex-1" />

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

        <span className="text-xs px-2 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-300 font-medium shrink-0 truncate max-w-[160px]">
          {fileName}
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
        <div
          onWheel={handleSlideWheel}
          title="Lăn chuột để chuyển trang"
          className="max-w-3xl mx-auto origin-top rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm hover:shadow-md transition-shadow overflow-hidden flex justify-center"
          style={{ transform: `scale(${zoom / 100})` }}
        >
          {pdfError ? (
            <div className="p-8 text-center text-sm text-rose-500">{pdfError}</div>
          ) : (
            fileUrl && (
              <PdfPage
                fileUrl={fileUrl}
                pageNumber={Math.min(currentPage, numPages || currentPage)}
                onLoadSuccess={(n) => {
                  setNumPages(n);
                  setPdfError(null);
                }}
                onLoadError={() => setPdfError("Không tải được file PDF từ backend.")}
              />
            )
          )}
        </div>

        {/* Khay xem text đã trích xuất (real, từ backend) */}
        <details
          open={showExtractedText}
          onToggle={(e) => setShowExtractedText(e.currentTarget.open)}
          className="max-w-3xl mx-auto mt-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800"
        >
          <summary className="cursor-pointer text-xs text-slate-500 dark:text-slate-400 px-4 py-2 select-none">
            Xem text đã trích xuất (để bôi đen hỏi AI)
          </summary>
          <div className="px-4 pb-4">
            {pageTextLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-3.5 w-full" />
                <Skeleton className="h-3.5 w-5/6" />
                <Skeleton className="h-3.5 w-3/4" />
              </div>
            ) : (
              <p
                onMouseUp={() => {
                  const sel = window.getSelection()?.toString().trim();
                  setSelectedText(sel && sel.length > 0 ? sel : "");
                }}
                className="select-text whitespace-pre-wrap text-[13px] text-slate-600 dark:text-slate-300 leading-relaxed"
              >
                {pageText || "Trang này không có text trích xuất được (có thể là slide dạng ảnh)."}
              </p>
            )}
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
            <MessageCircleQuestion className="w-4 h-4" /> Hỏi về trang {currentPage}
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
