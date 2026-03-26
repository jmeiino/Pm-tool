import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "danger" | "info" | "brand";
  className?: string;
}

const variantClasses = {
  default:
    "bg-surface-up border-[rgba(0,0,0,0.08)] text-inotec-muted before:bg-inotec-muted",
  success:
    "bg-[rgba(0,165,80,0.09)] border-[rgba(0,165,80,0.20)] text-[#007A37] before:bg-[#00A550]",
  warning:
    "bg-[rgba(217,119,6,0.09)] border-[rgba(217,119,6,0.20)] text-[#92520C] before:bg-[#D97706]",
  danger:
    "bg-[rgba(220,38,38,0.08)] border-[rgba(220,38,38,0.18)] text-[#B91C1C] before:bg-[#DC2626]",
  info:
    "bg-[rgba(59,130,246,0.08)] border-[rgba(59,130,246,0.20)] text-[#1D4ED8] before:bg-[#3B82F6]",
  brand:
    "bg-brand-muted border-brand-border text-brand-deeper before:bg-brand",
};

export function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 font-mono text-[0.70rem] font-medium uppercase tracking-wider before:h-1.5 before:w-1.5 before:rounded-full before:flex-shrink-0",
        variantClasses[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
