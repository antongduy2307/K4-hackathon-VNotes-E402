"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Sparkles, X } from "lucide-react";

type FlashcardFlipProps = {
  front: string;
  back: string;
  // "generating": AI đang trích xuất -> thẻ tự xoay lật liên tục kèm hiệu ứng phát sáng
  // "ready": đã có kết quả -> thẻ dừng lại, người dùng hover/click để xem 2 mặt
  status: "generating" | "ready";
  onClose: () => void;
};

// Overlay hiển thị thẻ Flashcard xoay lật 3D ở giữa màn hình, dùng khi AI đang tạo flashcard
export function FlashcardFlip({ front, back, status, onClose }: FlashcardFlipProps) {
  const [manualFlip, setManualFlip] = useState(false);
  const isGenerating = status === "generating";

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm"
        onClick={() => !isGenerating && onClose()}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.85, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.85, y: 20 }}
          transition={{ type: "spring", stiffness: 260, damping: 22 }}
          className="relative flex flex-col items-center gap-4"
          onClick={(e) => e.stopPropagation()}
        >
          {!isGenerating && (
            <button
              onClick={onClose}
              className="absolute -top-10 right-0 text-slate-200 hover:text-white transition"
              aria-label="Đóng"
            >
              <X className="w-5 h-5" />
            </button>
          )}

          {/* Vùng chứa thẻ, cần perspective để hiệu ứng 3D có chiều sâu */}
          <div className="[perspective:1200px] w-72 h-44 sm:w-80 sm:h-48">
            <motion.div
              className="relative w-full h-full [transform-style:preserve-3d] cursor-pointer"
              animate={
                isGenerating
                  ? { rotateY: [0, 360] }
                  : { rotateY: manualFlip ? 180 : 0 }
              }
              transition={
                isGenerating
                  ? { repeat: Infinity, duration: 1.3, ease: "linear" }
                  : { type: "spring", stiffness: 300, damping: 26 }
              }
              onHoverStart={() => !isGenerating && setManualFlip(true)}
              onHoverEnd={() => !isGenerating && setManualFlip(false)}
              onClick={() => !isGenerating && setManualFlip((v) => !v)}
            >
              {/* Viền phát sáng kiểu shimmer khi đang tạo thẻ */}
              {isGenerating && (
                <motion.div
                  className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-indigo-500 via-violet-500 to-fuchsia-500 blur-md"
                  animate={{ opacity: [0.4, 0.9, 0.4] }}
                  transition={{ repeat: Infinity, duration: 1.3, ease: "easeInOut" }}
                />
              )}

              {/* Mặt trước - Câu hỏi */}
              <div className="absolute inset-0 [backface-visibility:hidden] rounded-2xl border border-indigo-200 dark:border-indigo-800 bg-white dark:bg-slate-900 shadow-xl p-5 flex flex-col">
                <span className="text-[11px] font-semibold uppercase tracking-wide text-indigo-500 dark:text-indigo-400 flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5" />
                  {isGenerating ? "Đang tạo flashcard..." : "Mặt trước · Câu hỏi"}
                </span>
                <p className="mt-3 flex-1 flex items-center text-sm sm:text-base font-medium text-slate-800 dark:text-slate-100 leading-relaxed">
                  {isGenerating ? "AI đang đọc slide và soạn câu hỏi phù hợp..." : front}
                </p>
                {!isGenerating && (
                  <p className="text-[11px] text-slate-400">Di chuột hoặc bấm để lật thẻ</p>
                )}
              </div>

              {/* Mặt sau - Đáp án */}
              <div className="absolute inset-0 [backface-visibility:hidden] [transform:rotateY(180deg)] rounded-2xl border border-violet-200 dark:border-violet-800 bg-gradient-to-br from-indigo-600 to-violet-600 shadow-xl p-5 flex flex-col text-white">
                <span className="text-[11px] font-semibold uppercase tracking-wide text-indigo-100 flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5" />
                  Mặt sau · Đáp án
                </span>
                <p className="mt-3 flex-1 flex items-center text-sm sm:text-base font-medium leading-relaxed">
                  {back}
                </p>
              </div>
            </motion.div>
          </div>

          {isGenerating && (
            <p className="text-xs text-slate-100/90 bg-slate-900/40 px-3 py-1.5 rounded-full">
              AI đang trích xuất kiến thức trọng tâm từ slide này...
            </p>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
