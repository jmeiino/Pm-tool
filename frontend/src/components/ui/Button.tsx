import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes, forwardRef } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
}

const variantClasses = {
  primary:
    "bg-brand text-white hover:bg-brand-dark hover:-translate-y-px hover:shadow-brand",
  secondary:
    "bg-transparent text-inotec-text border border-[rgba(0,0,0,0.14)] hover:border-brand hover:text-brand hover:-translate-y-px",
  ghost:
    "text-inotec-muted hover:bg-surface-up hover:text-inotec-text",
  danger:
    "bg-[rgba(220,38,38,0.08)] text-[#B91C1C] border border-[rgba(220,38,38,0.18)] hover:bg-[rgba(220,38,38,0.14)] hover:-translate-y-px",
};

const sizeClasses = {
  sm: "min-h-[32px] px-4 text-[0.70rem]",
  md: "min-h-[40px] px-5 text-[0.72rem]",
  lg: "min-h-[44px] px-6 text-xs",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center gap-2 rounded-sm font-semibold uppercase tracking-wider transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-40 disabled:transform-none disabled:shadow-none",
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        disabled={disabled}
        {...props}
      />
    );
  }
);

Button.displayName = "Button";
