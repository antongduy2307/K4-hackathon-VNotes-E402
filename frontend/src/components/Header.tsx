"use client";

import { motion } from "framer-motion";
import { Moon, Sparkles, Sun, UploadCloud } from "lucide-react";
import { useTheme } from "@/lib/theme";

export function Header({ onOpenUpload }: { onOpenUpload: () => void }) {
  const { theme, toggle } = useTheme();

  return (
    <header className="h-14 flex items-center justify-between px-4 border-b border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/70 backdrop-blur-md">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white">
          <Sparkles className="w-4 h-4" />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-900 dark:text-white leading-tight">
            AI Slide Tutor
          </p>
          <p className="text-[11px] text-slate-400 leading-tight">Trợ lý Trích xuất Kiến thức</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.95 }}
          onClick={onOpenUpload}
          className="flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white transition shadow-sm"
        >
          <UploadCloud className="w-4 h-4" />
          Nhập PDF/Slide
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.06, rotate: 8 }}
          whileTap={{ scale: 0.9 }}
          onClick={toggle}
          title={theme === "light" ? "Chuyển sang Chế độ tối" : "Chuyển sang Chế độ sáng"}
          className="w-9 h-9 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center justify-center text-slate-600 dark:text-slate-300 transition"
        >
          {theme === "light" ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
        </motion.button>
      </div>
    </header>
  );
}
