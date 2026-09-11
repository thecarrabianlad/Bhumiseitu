import Link from "next/link";
import { getLandRecordById } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";
import {
  ChevronLeftIcon,
  DownloadIcon,
  FileTextIcon,
  FolderIcon,
  ImageIcon,
  MapPinIcon,
  UserIcon,
} from "@/components/icons";

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-ink-300">{label}</dt>
      <dd className="mt-1 text-sm font-medium text-ink-900">{value}</dd>
    </div>
  );
}

function SectionCard({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-md border border-border bg-surface shadow-card">
      <div className="flex items-center gap-2.5 border-b border-border px-5 py-3.5">
        <span className="flex h-7 w-7 items-center justify-center rounded-md bg-brand-50 text-brand-600">
          {icon}
        </span>
        <h2 className="text-sm font-semibold text-ink-900">{title}</h2>
      </div>
      <dl className="grid grid-cols-1 gap-5 px-5 py-5 sm:grid-cols-2">{children}</dl>
    </section>
  );
}

export default async function RecordDetailPage({ params }: { params: { id: string } }) {
  const record = await getLandRecordById(params.id);

  if (!record) {
    return (
      <div className="space-y-4">
        <Link href="/records" className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-600 hover:underline">
          <ChevronLeftIcon className="h-4 w-4" />
          Back to Land Records
        </Link>
        <EmptyState
          icon={<FolderIcon className="h-6 w-6" />}
          title="Record not found"
          description={`No land record exists with ID "${params.id}". It may have been removed or the link may be incorrect.`}
          action={
            <Link href="/records" className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
              Browse Land Records
            </Link>
          }
        />
      </div>
    );
  }

  const DocIcon = record.documentType === "PDF" ? FileTextIcon : ImageIcon;

  return (
    <div className="space-y-5">
      <Link href="/records" className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-600 hover:underline">
        <ChevronLeftIcon className="h-4 w-4" />
        Back to Land Records
      </Link>

      <div className="flex flex-col gap-3 rounded-md border border-border bg-surface p-5 shadow-card sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs text-ink-300">Land Record</p>
          <h2 className="mt-0.5 text-lg font-semibold tracking-tight text-ink-900">{record.id}</h2>
          <p className="mt-1 text-sm text-ink-500">
            {record.village}, {record.district}, {record.state}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge status={record.status} />
        </div>
      </div>

      <SectionCard title="Owner Information" icon={<UserIcon className="h-4 w-4" />}>
        <Field label="Owner Name" value={record.ownerName} />
        <Field label="Guardian / Father's Name" value={record.guardianName} />
      </SectionCard>

      <SectionCard title="Land &amp; Location Information" icon={<MapPinIcon className="h-4 w-4" />}>
        <Field label="Village" value={record.village} />
        <Field label="District" value={record.district} />
        <Field label="State" value={record.state} />
        <Field label="Land Type" value={record.landType} />
      </SectionCard>

      <SectionCard title="Survey &amp; Area Details" icon={<FolderIcon className="h-4 w-4" />}>
        <Field label="Survey / Khasra Number" value={record.khasraNumber} />
        <Field label="Khatauni Number" value={record.khatauniNumber} />
        <Field label="Area" value={`${record.areaValue} ${record.areaUnit}`} />
        <Field label="Estimated Market Value" value={formatCurrency(record.marketValueInr)} />
      </SectionCard>

      <SectionCard title="Registration Information" icon={<FileTextIcon className="h-4 w-4" />}>
        <Field label="Mutation Number" value={record.mutationNumber} />
        <Field label="Registration Date" value={formatDate(record.registrationDate)} />
        <Field label="Verification Status" value={<StatusBadge status={record.status} />} />
        <Field label="Last Updated" value={formatDate(record.lastUpdated)} />
      </SectionCard>

      <section className="rounded-md border border-border bg-surface shadow-card">
        <div className="flex items-center gap-2.5 border-b border-border px-5 py-3.5">
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-brand-50 text-brand-600">
            <DocIcon className="h-4 w-4" />
          </span>
          <h2 className="text-sm font-semibold text-ink-900">Document Information</h2>
        </div>
        <div className="flex flex-col gap-4 px-5 py-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-canvas text-ink-500 ring-1 ring-border">
              <DocIcon className="h-[18px] w-[18px]" />
            </div>
            <div>
              <p className="text-sm font-medium text-ink-900">{record.documentName}</p>
              <p className="text-xs text-ink-300">
                {record.documentType} &middot; {(record.documentSizeKb / 1024).toFixed(2)} MB
              </p>
            </div>
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              title="Mock action — not connected to a document store yet"
              className="inline-flex items-center gap-2 rounded-md border border-border-strong bg-surface px-4 py-2 text-sm font-medium text-ink-900 hover:bg-canvas"
            >
              View Document
            </button>
            <button
              type="button"
              title="Mock action — not connected to a document store yet"
              className="inline-flex items-center gap-2 rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
            >
              <DownloadIcon className="h-4 w-4" />
              Download
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
