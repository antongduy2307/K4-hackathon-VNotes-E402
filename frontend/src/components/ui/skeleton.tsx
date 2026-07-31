import { cn } from "@/lib/utils";

// Khối Skeleton dùng chung, tạo hiệu ứng "shimmer" chạy ngang khi đang tải dữ liệu
export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("skeleton-shimmer rounded-md", className)} />;
}
