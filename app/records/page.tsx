"use client";

import { useEffect, useMemo, useState } from "react";
import { getLandRecords } from "@/lib/api";
import { districtsByState, indianStates } from "@/lib/mockData";
import { LandRecord, RecordStatus } from "@/types/landRecord";
import SearchBar from "@/components/SearchBar";
import LandRecordTable from "@/components/LandRecordTable";
import EmptyState from "@/components/EmptyState";
import { ChevronLeftIcon, ChevronRightIcon, FolderIcon } from "@/components/icons";

const STATUS_OPTIONS: (RecordStatus | "All")[] = ["All", "Verified", "Pending", "Under Review", "Rejected"];
const PAGE_SIZE = 8;

const selectClasses =
  "rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink-900 focus:border-brand-600 focus:outline-none focus:ring-1 focus:ring-brand-600";

export default function RecordsPage() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<string>("All");
  const [state, setState] = useState<string>("All");
  const [district, setDistrict] = useState<string>("All");
  const [sortBy, setSortBy] = useState<keyof LandRecord>("lastUpdated");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  const [records, setRecords] = useState<LandRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const districtOptions = useMemo(
    () => (state === "All" ? [] : districtsByState[state] ?? []),
    [state]
  );

  // Reset to page 1 whenever a filter or search term changes.
  useEffect(() => {
    setPage(1);
  }, [query, status, state, district, sortBy, sortDirection]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    const handle = setTimeout(async () => {
      const result = await getLandRecords({
        query,
        status,
        state,
        district,
        page,
        pageSize: PAGE_SIZE,
        sortBy,
        sortDirection,
      });
      if (!cancelled) {
        setRecords(result.records);
        setTotal(result.total);
        setLoading(false);
      }
    }, 200);

    return () => {
      cancelled = true;
      clearTimeout(handle);
    };
  }, [query, status, state, district, page, sortBy, sortDirection]);

  function handleSortChange(key: keyof LandRecord) {
    if (sortBy === key) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(key);
      setSortDirection("asc");
    }
  }

  function handleStateChange(value: string) {
    setState(value);
    setDistrict("All");
  }

  function handleClearFilters() {
    setQuery("");
    setStatus("All");
    setState("All");
    setDistrict("All");
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const hasActiveFilters = query !== "" || status !== "All" || state !== "All" || district !== "All";
  const rangeStart = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const rangeEnd = Math.min(page * PAGE_SIZE, total);

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 rounded-md border border-border bg-surface p-4 shadow-card sm:flex-row sm:flex-wrap sm:items-center">
        <div className="sm:w-72">
          <SearchBar
            value={query}
            onChange={setQuery}
            placeholder="Search by owner, record ID, village, khasra no."
          />
        </div>

        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          aria-label="Filter by status"
          className={selectClasses}
        >
          {STATUS_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option === "All" ? "All statuses" : option}
            </option>
          ))}
        </select>

        <select
          value={state}
          onChange={(e) => handleStateChange(e.target.value)}
          aria-label="Filter by state"
          className={selectClasses}
        >
          <option value="All">All states</option>
          {indianStates.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>

        <select
          value={district}
          onChange={(e) => setDistrict(e.target.value)}
          aria-label="Filter by district"
          disabled={state === "All"}
          className={`${selectClasses} disabled:cursor-not-allowed disabled:opacity-50`}
        >
          <option value="All">All districts</option>
          {districtOptions.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>

        {hasActiveFilters && (
          <button
            onClick={handleClearFilters}
            className="text-sm font-medium text-brand-600 hover:text-brand-700 hover:underline sm:ml-auto"
          >
            Clear filters
          </button>
        )}
      </div>

      {loading ? (
        <div className="rounded-md border border-border bg-surface p-10 text-center text-sm text-ink-300 shadow-card">
          Loading records…
        </div>
      ) : records.length === 0 ? (
        <EmptyState
          icon={<FolderIcon className="h-6 w-6" />}
          title="No matching land records"
          description="Try adjusting your search term or clearing the active filters to see more results."
          action={
            hasActiveFilters ? (
              <button
                onClick={handleClearFilters}
                className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
              >
                Clear filters
              </button>
            ) : undefined
          }
        />
      ) : (
        <>
          <LandRecordTable
            records={records}
            variant="full"
            sortBy={sortBy}
            sortDirection={sortDirection}
            onSortChange={handleSortChange}
          />

          <div className="flex flex-col items-center justify-between gap-3 sm:flex-row">
            <p className="text-sm text-ink-500">
              Showing <span className="font-medium text-ink-900">{rangeStart}–{rangeEnd}</span> of{" "}
              <span className="font-medium text-ink-900">{total}</span> records
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                aria-label="Previous page"
                className="flex h-8 w-8 items-center justify-center rounded-md border border-border bg-surface text-ink-500 hover:bg-canvas disabled:cursor-not-allowed disabled:opacity-50"
              >
                <ChevronLeftIcon className="h-4 w-4" />
              </button>
              <span className="min-w-[5.5rem] text-center text-sm text-ink-500">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                aria-label="Next page"
                className="flex h-8 w-8 items-center justify-center rounded-md border border-border bg-surface text-ink-500 hover:bg-canvas disabled:cursor-not-allowed disabled:opacity-50"
              >
                <ChevronRightIcon className="h-4 w-4" />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
