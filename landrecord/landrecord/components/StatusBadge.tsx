import { RecordStatus } from "@/types/landRecord";
import { AlertIcon, CheckCircleIcon, ClockIcon, XCircleIcon } from "@/components/icons";

const STATUS_STYLES: Record<
  RecordStatus,
  { text: string; bg: string; icon: (props: { className?: string }) => JSX.Element }
> = {
  Verified: { text: "text-status-verified", bg: "bg-status-verifiedBg", icon: CheckCircleIcon },
  Pending: { text: "text-status-pending", bg: "bg-status-pendingBg", icon: ClockIcon },
  "Under Review": { text: "text-status-review", bg: "bg-status-reviewBg", icon: AlertIcon },
  Rejected: { text: "text-status-rejected", bg: "bg-status-rejectedBg", icon: XCircleIcon },
};

export default function StatusBadge({ status }: { status: RecordStatus }) {
  const style = STATUS_STYLES[status];
  const Icon = style.icon;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${style.text} ${style.bg}`}
    >
      <Icon className="h-3.5 w-3.5" />
      {status}
    </span>
  );
}
