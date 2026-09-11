import { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: string | number;
  icon: ReactNode;
  accent: "brand" | "verified" | "pending" | "review";
  helperText?: string;
}

const ACCENT_STYLES: Record<StatCardProps["accent"], { iconBg: string; iconText: string; bar: string }> = {
  brand: { iconBg: "bg-brand-50", iconText: "text-brand-600", bar: "bg-brand-600" },
  verified: { iconBg: "bg-status-verifiedBg", iconText: "text-status-verified", bar: "bg-status-verified" },
  pending: { iconBg: "bg-status-pendingBg", iconText: "text-status-pending", bar: "bg-status-pending" },
  review: { iconBg: "bg-status-reviewBg", iconText: "text-status-review", bar: "bg-status-review" },
};

export default function StatCard({ label, value, icon, accent, helperText }: StatCardProps) {
  const styles = ACCENT_STYLES[accent];
  return (
    <div className="relative overflow-hidden rounded-md border border-border bg-surface p-5 shadow-card">
      <span className={`absolute inset-y-0 left-0 w-1 ${styles.bar}`} aria-hidden />
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-ink-500">{label}</p>
          <p className="mt-2 text-2xl font-semibold tracking-tight text-ink-900">{value}</p>
          {helperText && <p className="mt-1 text-xs text-ink-300">{helperText}</p>}
        </div>
        <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-md ${styles.iconBg} ${styles.iconText}`}>
          {icon}
        </div>
      </div>
    </div>
  );
}
