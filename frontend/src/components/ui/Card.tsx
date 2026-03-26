import { cn } from "@/lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  action?: React.ReactNode;
}

export function Card({ children, className, title, action }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-md border border-[rgba(0,0,0,0.08)] bg-white shadow-sm transition-all duration-200 hover:shadow-md hover:border-brand-border hover:-translate-y-0.5",
        className
      )}
    >
      {title && (
        <div className="flex items-center justify-between border-b border-[rgba(0,0,0,0.08)] px-5 py-3">
          <h3 className="text-sm font-semibold text-inotec-text tracking-wide">
            {title}
          </h3>
          {action}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
}
