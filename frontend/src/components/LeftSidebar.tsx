"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ChevronDown, ChevronRight, Download, FileText, Layers } from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import type { ContentNode, ReviewStats, SavedFlashcard, SavedNote } from "@/lib/types";

type LeftSidebarProps = {
  fileName: string;
  totalLessons: number;
  reviewStats: ReviewStats;
  contentTree: ContentNode[];
  activeNodeId: string;
  onSelectNode: (id: string) => void;
  notes: SavedNote[];
  flashcards: SavedFlashcard[];
  onExportNotes: () => void;
  onExportFlashcards: () => void;
};

export function LeftSidebar({
  fileName,
  totalLessons,
  reviewStats,
  contentTree,
  activeNodeId,
  onSelectNode,
  notes,
  flashcards,
  onExportNotes,
  onExportFlashcards,
}: LeftSidebarProps) {
  return (
    <aside className="w-full h-full flex flex-col bg-white dark:bg-slate-900">
      {/* Thương hiệu */}
      <div className="p-4 border-b border-slate-100 dark:border-slate-800">
        <p className="text-xs font-medium text-indigo-600 dark:text-indigo-400 uppercase tracking-wide">
          AI Slide Tutor
        </p>
        <h1 className="text-base font-semibold text-slate-900 dark:text-white mt-0.5">
          Trợ lý Trích xuất Kiến thức
        </h1>
        <p className="text-[11px] text-slate-400 mt-1">
          Nguồn: <code className="bg-slate-100 dark:bg-slate-800 px-1 rounded">{fileName}</code> ·{" "}
          {totalLessons} bài học
        </p>
      </div>

      {/* Lịch ôn tập ngắt quãng */}
      <div className="px-3 py-3 border-b border-slate-100 dark:border-slate-800">
        <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-2">
          Lịch ôn tập ngắt quãng
        </p>
        <div className="grid grid-cols-3 gap-1.5">
          <StatTile label="Hôm nay" value={reviewStats.today} tone="rose" />
          <StatTile label="3 ngày" value={reviewStats.in3Days} tone="amber" />
          <StatTile label="7 ngày" value={reviewStats.in7Days} tone="emerald" />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Cây nội dung khoá học */}
        <div className="px-3 pt-3 pb-1">
          <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">
            Nội dung khoá học
          </p>
        </div>
        <div className="px-2 text-sm">
          {contentTree.map((node) => {
            const isActive = node.id === activeNodeId;
            const Icon = node.kind === "transcript" ? FileText : Layers;
            return (
              <motion.button
                key={node.id}
                onClick={() => onSelectNode(node.id)}
                whileHover={{ x: 3 }}
                whileTap={{ scale: 0.98 }}
                transition={{ type: "spring", stiffness: 400, damping: 28 }}
                className={cn(
                  "w-full flex items-center gap-2 px-2.5 py-2 rounded-lg text-left text-[13px] transition-colors mb-0.5 border",
                  isActive
                    ? "bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 font-medium border-indigo-200 dark:border-indigo-800"
                    : "text-slate-600 dark:text-slate-300 border-transparent hover:bg-slate-50 dark:hover:bg-slate-800 hover:border-indigo-100 dark:hover:border-indigo-900"
                )}
              >
                <Icon className="w-3.5 h-3.5 shrink-0" />
                <span className="truncate">{node.label}</span>
                {isActive ? (
                  <ChevronDown className="ml-auto w-3.5 h-3.5 shrink-0" />
                ) : (
                  <ChevronRight className="ml-auto w-3.5 h-3.5 shrink-0 opacity-0" />
                )}
              </motion.button>
            );
          })}
        </div>

        {/* Kho lưu trữ */}
        <div className="px-3 pt-4 pb-1 mt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">
            Kho lưu trữ
          </p>
          <div className="flex gap-2">
            <button
              onClick={onExportNotes}
              className="text-[10px] text-indigo-600 dark:text-indigo-400 hover:underline font-medium flex items-center gap-0.5"
            >
              <Download className="w-2.5 h-2.5" /> Ghi chú
            </button>
            <button
              onClick={onExportFlashcards}
              className="text-[10px] text-indigo-600 dark:text-indigo-400 hover:underline font-medium flex items-center gap-0.5"
            >
              <Download className="w-2.5 h-2.5" /> Anki
            </button>
          </div>
        </div>

        <div className="px-2 pb-4 space-y-1.5">
          {/* activeNodeId đổi -> remount ArchiveGate -> tự phát lại hiệu ứng Skeleton khi chuyển bài học */}
          <ArchiveGate switchKey={activeNodeId}>
            {notes.length === 0 && flashcards.length === 0 && (
              <p className="text-[12px] text-slate-400 italic px-1">
                Chưa có ghi chú/flashcard nào — dùng &quot;Tóm tắt&quot; hoặc &quot;Tóm gọn kiến
                thức&quot; để lưu.
              </p>
            )}
            {notes.map((note, i) => (
              <motion.div
                key={note.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                className="border border-slate-100 dark:border-slate-800 rounded-lg p-2.5 hover:border-indigo-200 dark:hover:border-indigo-800 transition-colors"
              >
                <div className="flex items-center gap-1.5 mb-1">
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 font-medium">
                    Ghi chú
                  </span>
                  <span className="text-[10px] text-slate-400 truncate">{note.title}</span>
                </div>
                <p className="text-[12px] text-slate-600 dark:text-slate-300 line-clamp-2">
                  {note.snippet}
                </p>
              </motion.div>
            ))}
            {flashcards.map((card, i) => (
              <motion.div
                key={card.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                className="border border-slate-100 dark:border-slate-800 rounded-lg p-2.5 hover:border-violet-200 dark:hover:border-violet-800 transition-colors"
              >
                <div className="flex items-center gap-1.5 mb-1">
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-300 font-medium">
                    Flashcard
                  </span>
                </div>
                <p className="text-[12px] font-medium text-slate-700 dark:text-slate-200 line-clamp-1">
                  {card.front}
                </p>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-1">
                  {card.back}
                </p>
              </motion.div>
            ))}
          </ArchiveGate>
        </div>
      </div>
    </aside>
  );
}

const toneClasses = {
  rose: "bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-300",
  amber: "bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-300",
  emerald: "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-300",
};

function StatTile({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: keyof typeof toneClasses;
}) {
  return (
    <div className={cn("rounded-lg px-1.5 py-2 text-center", toneClasses[tone])}>
      <p className="text-base font-bold leading-none">{value}</p>
      <p className="text-[9px] mt-1 font-medium opacity-80">{label}</p>
    </div>
  );
}

// Hiển thị Skeleton trong chốc lát mỗi khi người dùng chuyển bài học, tạo cảm giác đang tải nội dung.
// Dùng "key" để ép remount thay vì gọi setState trực tiếp trong effect (tránh cascading render).
function ArchiveGate({ switchKey, children }: { switchKey: string; children: React.ReactNode }) {
  return <ArchiveGateFrame key={switchKey}>{children}</ArchiveGateFrame>;
}

function ArchiveGateFrame({ children }: { children: React.ReactNode }) {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 320);
    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return (
      <>
        <Skeleton className="h-14 w-full rounded-lg" />
        <Skeleton className="h-14 w-full rounded-lg" />
      </>
    );
  }

  return <>{children}</>;
}
