import { cn } from "@/utils/cn";

export function KpiCard({
  title,
  value,
  tone = "default",
  className
}: {
  title: string;
  value: string;
  tone?: "default" | "escrow" | "alert";
  className?: string;
}) {
  const ring =
    tone === "escrow"
      ? "ring-1 ring-escrow-light/40"
      : tone === "alert"
        ? "ring-1 ring-alert-pending/50"
        : "ring-1 ring-agro-leaf/35";

  return (
    <div
      className={cn(
        "rounded-[14px] bg-white p-4 shadow-card-soft",
        ring,
        className
      )}
    >
      <div className="text-xs text-slate-600">{title}</div>
      <div className="mt-1 text-lg font-semibold tracking-[-0.01em]">{value}</div>
    </div>
  );
}
