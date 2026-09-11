import Link from "next/link";
import { getDashboardStats, getLandRecords, getRecentUploads } from "@/lib/api";
import StatCard from "@/components/StatCard";
import LandRecordTable from "@/components/LandRecordTable";
import { CheckCircleIcon, ClockIcon, FileTextIcon, LayersIcon, UploadIcon } from "@/components/icons";

const UPLOAD_STATUS_STYLES: Record<string, string> = {
  Processed: "text-status-verified bg-status-verifiedBg",
  Processing: "text-status-pending bg-status-pendingBg",
  Failed: "text-status-rejected bg-status-rejectedBg",
};

function formatRelativeUpload(iso: string) {
  const date = new Date(iso);
  const diffMs = Date.now() - date.getTime();
  const diffHours = Math.round(diffMs / 3600000);
  if (diffHours < 1) return "Just now";
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.round(diffHours / 24);
  return `${diffDays}d ago`;
}

export default async function DashboardPage() {
  const [stats, recentRecords, recentUploads] = await Promise.all([
    getDashboardStats(),
    getLandRecords({ sortBy: "lastUpdated", sortDirection: "desc", pageSize: 5 }),
    getRecentUploads(),
  ]);

  return (
    <div className="space-y-6">
      <section aria-label="Summary statistics" className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total Land Records"
          value={stats.totalRecords.toLocaleString("en-IN")}
          icon={<LayersIcon className="h-5 w-5" />}
          accent="brand"
          helperText="Digitized in the registry"
        />
        <StatCard
          label="Verified Records"
          value={stats.verifiedRecords.toLocaleString("en-IN")}
          icon={<CheckCircleIcon className="h-5 w-5" />}
          accent="verified"
          helperText="Confirmed by field officers"
        />
        <StatCard
          label="Pending Records"
          value={stats.pendingRecords.toLocaleString("en-IN")}
          icon={<ClockIcon className="h-5 w-5" />}
          accent="pending"
          helperText="Awaiting verification"
        />
        <StatCard
          label="Documents Uploaded"
          value={stats.documentsUploaded.toLocaleString("en-IN")}
          icon={<FileTextIcon className="h-5 w-5" />}
          accent="review"
          helperText="Scans and deeds on file"
        />
      </section>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <section className="lg:col-span-2" aria-labelledby="recent-records-heading">
          <div className="mb-3 flex items-center justify-between">
            <h2 id="recent-records-heading" className="text-sm font-semibold text-ink-900">
              Recent Land Records
            </h2>
            <Link
              href="/upload"
              className="inline-flex items-center gap-2 rounded-md bg-brand-600 px-3.5 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-700"
            >
              <UploadIcon className="h-4 w-4" />
              Upload Document
            </Link>
          </div>
          <LandRecordTable records={recentRecords.records} variant="compact" />
          <div className="mt-3 text-right">
            <Link href="/records" className="text-sm font-medium text-brand-600 hover:text-brand-700 hover:underline">
              View all land records
            </Link>
          </div>
        </section>

        <section aria-labelledby="recent-activity-heading">
          <h2 id="recent-activity-heading" className="mb-3 text-sm font-semibold text-ink-900">
            Recent Uploads
          </h2>
          <div className="rounded-md border border-border bg-surface shadow-card">
            <ul className="divide-y divide-border">
              {recentUploads.map((upload) => (
                <li key={upload.id} className="flex items-start gap-3 px-4 py-3.5">
                  <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-brand-50 text-brand-600">
                    <FileTextIcon className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-ink-900">{upload.fileName}</p>
                    <p className="mt-0.5 text-xs text-ink-300">
                      Linked to{" "}
                      <Link href={`/records/${upload.relatedRecordId}`} className="text-brand-600 hover:underline">
                        {upload.relatedRecordId}
                      </Link>
                      {" · "}
                      {formatRelativeUpload(upload.uploadedAt)}
                    </p>
                  </div>
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium ${UPLOAD_STATUS_STYLES[upload.status]}`}
                  >
                    {upload.status}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </section>
      </div>
    </div>
  );
}
