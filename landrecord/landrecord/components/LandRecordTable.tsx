"use client";

import Link from "next/link";
import { LandRecord } from "@/types/landRecord";
import StatusBadge from "@/components/StatusBadge";
import { ArrowUpDownIcon } from "@/components/icons";

interface Column {
  key: keyof LandRecord | "location" | "area" | "actions";
  label: string;
  sortable?: boolean;
}

const FULL_COLUMNS: Column[] = [
  { key: "id", label: "Record ID", sortable: true },
  { key: "ownerName", label: "Owner", sortable: true },
  { key: "location", label: "Village / District" },
  { key: "khasraNumber", label: "Survey / Khasra No." },
  { key: "area", label: "Area" },
  { key: "status", label: "Status", sortable: true },
  { key: "lastUpdated", label: "Last Updated", sortable: true },
];

const COMPACT_COLUMNS: Column[] = [
  { key: "id", label: "Record ID" },
  { key: "ownerName", label: "Owner" },
  { key: "location", label: "Village / District" },
  { key: "status", label: "Status" },
];

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

interface LandRecordTableProps {
  records: LandRecord[];
  variant?: "full" | "compact";
  sortBy?: keyof LandRecord;
  sortDirection?: "asc" | "desc";
  onSortChange?: (key: keyof LandRecord) => void;
}

export default function LandRecordTable({
  records,
  variant = "full",
  sortBy,
  sortDirection,
  onSortChange,
}: LandRecordTableProps) {
  const columns = variant === "full" ? FULL_COLUMNS : COMPACT_COLUMNS;

  return (
    <div className="overflow-hidden rounded-md border border-border bg-surface shadow-card">
      <div className="overflow-x-auto thin-scroll">
        <table className="w-full min-w-[720px] border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-border bg-canvas">
              {columns.map((col) => {
                const canSort = col.sortable && onSortChange && col.key !== "location" && col.key !== "area" && col.key !== "actions";
                const active = canSort && sortBy === col.key;
                return (
                  <th key={col.key} scope="col" className="px-4 py-3 font-medium text-ink-500">
                    {canSort ? (
                      <button
                        onClick={() => onSortChange!(col.key as keyof LandRecord)}
                        className="flex items-center gap-1.5 hover:text-ink-900"
                      >
                        {col.label}
                        <ArrowUpDownIcon
                          className={`h-3.5 w-3.5 ${active ? "text-brand-600" : "text-ink-300"}`}
                        />
                        {active && <span className="sr-only">({sortDirection})</span>}
                      </button>
                    ) : (
                      col.label
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {records.map((record) => (
              <tr
                key={record.id}
                className="border-b border-border last:border-0 hover:bg-canvas"
              >
                {columns.map((col) => (
                  <td key={col.key} className="px-4 py-3.5 align-middle text-ink-700">
                    {renderCell(col.key, record)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function renderCell(key: Column["key"], record: LandRecord) {
  switch (key) {
    case "id":
      return (
        <Link href={`/records/${record.id}`} className="font-medium text-brand-600 hover:text-brand-700 hover:underline">
          {record.id}
        </Link>
      );
    case "ownerName":
      return <span className="font-medium text-ink-900">{record.ownerName}</span>;
    case "location":
      return (
        <span>
          {record.village}
          <span className="text-ink-300"> / </span>
          {record.district}
        </span>
      );
    case "khasraNumber":
      return record.khasraNumber;
    case "area":
      return `${record.areaValue} ${record.areaUnit}`;
    case "status":
      return <StatusBadge status={record.status} />;
    case "lastUpdated":
      return formatDate(record.lastUpdated);
    default:
      return null;
  }
}
