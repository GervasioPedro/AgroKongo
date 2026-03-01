import * as React from "react";

import { cn } from "@/utils/cn";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
}

export function Input({ className, error, ...props }: InputProps) {
  return (
    <div className="w-full">
      <input
        className={cn(
          "h-11 w-full rounded-[var(--radius-button)] border bg-white px-4 text-base outline-none",
          "border-slate-200 focus:border-agro-leaf focus:ring-2 focus:ring-agro-leaf/30",
          error ? "border-alert-critical focus:border-alert-critical focus:ring-alert-critical/30" : "",
          className
        )}
        {...props}
      />
      {error ? <p className="mt-1 text-sm text-alert-critical">{error}</p> : null}
    </div>
  );
}
