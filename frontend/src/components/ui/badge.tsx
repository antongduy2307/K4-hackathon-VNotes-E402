import { type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type BadgeVariant = "purple" | "green" | "slate" | "red";

const variantClasses: Record<BadgeVariant, string> = {
  purple: "bg-[#ede9fe] text-[#5b21b6]",
  green: "bg-emerald-50 text-emerald-700",
  slate: "bg-slate-100 text-slate-600",
  red: "bg-rose-50 text-rose-600",
};

export function Badge({
  className,
  variant = "slate",
  ...props
}: HTMLAttributes<HTMLSpanElement> & { variant?: BadgeVariant }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium",
        variantClasses[variant],
        className
      )}
      {...props}
    />
  );
}
