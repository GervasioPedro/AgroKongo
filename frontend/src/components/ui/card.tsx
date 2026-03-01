import * as React from "react";

import { cn } from "@/utils/cn";

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-[var(--radius-card)] bg-white shadow-card-soft p-6",
        className
      )}
      {...props}
    />
  );
}
