"use client";

import { Separator } from "react-resizable-panels";
import { GripVertical } from "lucide-react";

// Thanh phân cách dùng để kéo giãn chiều rộng giữa các cột.
// "data-separator" do react-resizable-panels tự gán, nhận các giá trị: inactive | focus | active | disabled
export function ResizeHandle() {
  return (
    <Separator
      className="group relative w-2.5 shrink-0 flex items-center justify-center bg-transparent outline-none"
    >
      {/* Đường kẻ mảnh ở giữa, đổi màu khi hover hoặc đang kéo */}
      <div className="pointer-events-none absolute inset-y-0 left-1/2 w-px -translate-x-1/2 bg-slate-200 dark:bg-slate-800 transition-colors group-hover:bg-indigo-400 dark:group-hover:bg-indigo-500 group-data-[separator=active]:bg-indigo-500" />

      {/* Núm kéo hình viên thuốc với icon chấm, chỉ hiện rõ khi hover/kéo để không gây rối mắt */}
      <div className="pointer-events-none z-10 flex h-9 w-4 items-center justify-center rounded-full border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-400 opacity-0 shadow-sm transition-all duration-150 group-hover:opacity-100 group-data-[separator=active]:opacity-100 group-data-[separator=active]:border-indigo-400 group-data-[separator=active]:text-indigo-500">
        <GripVertical className="h-3 w-3" />
      </div>
    </Separator>
  );
}
