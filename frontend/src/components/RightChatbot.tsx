"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, Bot, Send, Sparkles, User } from "lucide-react";
import { cn } from "@/lib/utils";
import type { AgentStatus, ChatMessage } from "@/lib/types";

type RightChatbotProps = {
  agentStatus: AgentStatus;
  messages: ChatMessage[];
  onSendMessage: (text: string) => void;
  isGenerating?: boolean;
  onSummarizeConversation: () => void;
  insight?: string;
};

// Regex nhận diện các trích dẫn dạng [D1-p13] trong nội dung tin nhắn để tô sáng thành badge
const CITATION_PATTERN = /(\[[A-Za-z0-9-]{2,20}\])/g;

// Tách nội dung tin nhắn thành từng câu để tạo hiệu ứng xuất hiện tuần tự (fade-in từng câu)
function splitIntoSentences(content: string): string[] {
  const parts = content.match(/[^.!?\n]+[.!?\n]*/g);
  return parts && parts.length > 0 ? parts : [content];
}

function MessageBubbleContent({ content }: { content: string }) {
  const sentences = splitIntoSentences(content);
  return (
    <motion.span
      initial="hidden"
      animate="visible"
      variants={{ visible: { transition: { staggerChildren: 0.06 } } }}
    >
      {sentences.map((sentence, si) => (
        <motion.span
          key={si}
          variants={{
            hidden: { opacity: 0, y: 4 },
            visible: { opacity: 1, y: 0 },
          }}
          transition={{ duration: 0.25, ease: "easeOut" }}
        >
          {sentence.split(CITATION_PATTERN).map((chunk, ci) =>
            // split() với 1 nhóm capture sẽ đặt phần trích dẫn vào các vị trí lẻ (1, 3, 5...)
            ci % 2 === 1 ? (
              <span
                key={ci}
                className="citation-glow inline-block mx-0.5 px-1.5 py-0.5 rounded-full bg-indigo-600/10 text-indigo-600 dark:text-indigo-300 dark:bg-indigo-400/10 border border-indigo-200 dark:border-indigo-800 text-[10px] font-mono transition-shadow duration-200"
              >
                {chunk}
              </span>
            ) : (
              chunk
            )
          )}
        </motion.span>
      ))}
    </motion.span>
  );
}

export function RightChatbot({
  agentStatus,
  messages,
  onSendMessage,
  isGenerating,
  onSummarizeConversation,
  insight,
}: RightChatbotProps) {
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  function handleSend() {
    const text = draft.trim();
    if (!text || isGenerating) return;
    onSendMessage(text);
    setDraft("");
  }

  return (
    <aside className="w-full h-full flex flex-col bg-white dark:bg-slate-900">
      {/* Phần đầu - thông tin trợ lý AI */}
      <div className="h-14 flex items-center gap-2.5 px-3 border-b border-slate-200 dark:border-slate-800 shrink-0">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white shrink-0">
          <Bot className="w-4 h-4" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-slate-900 dark:text-white leading-tight">
            Trợ lý Học tập AI
          </p>
          <p className="text-[11px] text-emerald-600 dark:text-emerald-400 leading-tight">
            {agentStatus.mode} · {agentStatus.model} · {agentStatus.online ? "Đang hoạt động" : "Ngoại tuyến"}
          </p>
        </div>
      </div>

      {/* Cảnh báo insight thực tế */}
      {insight && (
        <div className="px-3 pt-3 shrink-0">
          <div className="w-full text-left text-[11px] px-2.5 py-2 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-100 dark:border-rose-900 text-rose-700 dark:text-rose-300 flex items-start gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <span>{insight}</span>
          </div>
        </div>
      )}

      {/* Dòng chảy hội thoại */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 py-3 space-y-3 text-sm">
        <AnimatePresence initial={false}>
          {messages.map((m) => (
            <motion.div
              key={m.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25, ease: "easeOut" }}
              className={cn("flex gap-2", m.role === "user" ? "justify-end" : "justify-start")}
            >
              {m.role === "assistant" && (
                <div className="w-6 h-6 rounded-full bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-300" />
                </div>
              )}
              <div className="max-w-[85%]">
                <div
                  className={cn(
                    "rounded-2xl px-3.5 py-2 text-[13px] leading-relaxed whitespace-pre-wrap",
                    m.role === "user"
                      ? "bg-indigo-600 text-white rounded-tr-sm"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 rounded-tl-sm"
                  )}
                >
                  <MessageBubbleContent content={m.content} />
                </div>
                <p
                  className={cn(
                    "mt-1 text-[10px] text-slate-400",
                    m.role === "user" ? "text-right" : "text-left"
                  )}
                >
                  {m.createdAt}
                </p>
              </div>
              {m.role === "user" && (
                <div className="w-6 h-6 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-3.5 h-3.5 text-slate-500 dark:text-slate-300" />
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
        {isGenerating && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex gap-2 justify-start"
          >
            <div className="w-6 h-6 rounded-full bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center shrink-0 mt-0.5">
              <Bot className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-300" />
            </div>
            <div className="rounded-2xl rounded-tl-sm bg-slate-100 dark:bg-slate-800 px-3.5 py-2.5 text-[13px] text-slate-400 flex items-center gap-1">
              <motion.span
                className="w-1.5 h-1.5 rounded-full bg-slate-400"
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{ repeat: Infinity, duration: 1, delay: 0 }}
              />
              <motion.span
                className="w-1.5 h-1.5 rounded-full bg-slate-400"
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{ repeat: Infinity, duration: 1, delay: 0.15 }}
              />
              <motion.span
                className="w-1.5 h-1.5 rounded-full bg-slate-400"
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{ repeat: Infinity, duration: 1, delay: 0.3 }}
              />
            </div>
          </motion.div>
        )}
      </div>

      {/* Nút hành động chính - dán ở dưới cùng */}
      <div className="px-3 shrink-0">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.97 }}
          onClick={onSummarizeConversation}
          className="w-full font-semibold px-3 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 text-white hover:opacity-90 transition flex items-center justify-center gap-1.5 shadow-sm"
        >
          <Sparkles className="w-4 h-4" /> Tóm gọn kiến thức hội thoại
        </motion.button>
      </div>

      <div className="p-3 border-t border-slate-100 dark:border-slate-800 mt-2 shrink-0">
        <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 rounded-xl px-3 py-2 focus-within:ring-2 focus-within:ring-indigo-300 dark:focus-within:ring-indigo-700 transition-shadow">
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                handleSend();
              }
            }}
            disabled={isGenerating}
            placeholder="Nhập câu hỏi của bạn..."
            className="flex-1 bg-transparent outline-none text-sm placeholder:text-slate-400 disabled:opacity-50 dark:text-white"
          />
          <motion.button
            whileHover={{ scale: 1.08 }}
            whileTap={{ scale: 0.9 }}
            onClick={handleSend}
            disabled={isGenerating || !draft.trim()}
            className="w-7 h-7 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white flex items-center justify-center shrink-0"
          >
            <Send className="w-3.5 h-3.5" />
          </motion.button>
        </div>
        <p className="text-[11px] text-slate-400 mt-1.5 text-center">
          Trả lời bám sát nội dung slide · căn cứ trên tài liệu
        </p>
      </div>
    </aside>
  );
}
