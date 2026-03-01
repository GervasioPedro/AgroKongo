import { cn } from "@/utils/cn";

type Step = {
  label: string;
  state: "done" | "active" | "todo";
};

export function StepIndicator({ steps, className }: { steps: Step[]; className?: string }) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      {steps.map((s, idx) => {
        const color =
          s.state === "done"
            ? "bg-agro-leaf"
            : s.state === "active"
              ? "bg-escrow-light"
              : "bg-slate-300";

        return (
          <div key={idx} className="flex items-center gap-2">
            <div className={cn("h-2.5 w-2.5 rounded-full", color)} />
            <span
              className={cn(
                "text-xs",
                s.state === "todo" ? "text-slate-500" : "text-slate-800"
              )}
            >
              {s.label}
            </span>
            {idx < steps.length - 1 ? <div className="h-px w-6 bg-slate-200" /> : null}
          </div>
        );
      })}
    </div>
  );
}
