import { landRecords, recentUploads } from "@/lib/mockData";
import { DashboardStats, LandRecord, RecentUpload } from "@/types/landRecord";

/**
 * Data access layer.
 *
 * Every function here currently reads from the local mock dataset in
 * lib/mockData.ts and resolves through a small artificial delay so the UI
 * can exercise its loading states honestly.
 *
 * When the FastAPI backend is available, swap the body of each function for
 * a `fetch` call against the matching endpoint. The function signatures are
 * written so that call sites in components/pages should not need to change.
 */

const SIMULATED_LATENCY_MS = 350;

function delay<T>(value: T, ms: number = SIMULATED_LATENCY_MS): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

// TODO(FastAPI): Set from NEXT_PUBLIC_API_BASE_URL once the backend exists.
// export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export interface GetLandRecordsParams {
  query?: string;
  status?: string;
  state?: string;
  district?: string;
  page?: number;
  pageSize?: number;
  sortBy?: keyof LandRecord;
  sortDirection?: "asc" | "desc";
}

export interface GetLandRecordsResult {
  records: LandRecord[];
  total: number;
  page: number;
  pageSize: number;
}

/**
 * Fetch a paginated, filtered, sorted list of land records.
 *
 * TODO(FastAPI): Replace with:
 *   const res = await fetch(`${API_BASE_URL}/api/records?${new URLSearchParams({...})}`);
 *   if (!res.ok) throw new Error("Failed to load land records");
 *   return res.json();
 */
export async function getLandRecords(
  params: GetLandRecordsParams = {}
): Promise<GetLandRecordsResult> {
  const {
    query = "",
    status = "All",
    state = "All",
    district = "All",
    page = 1,
    pageSize = 8,
    sortBy = "lastUpdated",
    sortDirection = "desc",
  } = params;

  let results = [...landRecords];

  if (query.trim()) {
    const q = query.trim().toLowerCase();
    results = results.filter(
      (r) =>
        r.ownerName.toLowerCase().includes(q) ||
        r.id.toLowerCase().includes(q) ||
        r.village.toLowerCase().includes(q) ||
        r.khasraNumber.toLowerCase().includes(q)
    );
  }

  if (status !== "All") {
    results = results.filter((r) => r.status === status);
  }

  if (state !== "All") {
    results = results.filter((r) => r.state === state);
  }

  if (district !== "All") {
    results = results.filter((r) => r.district === district);
  }

  results.sort((a, b) => {
    const aVal = a[sortBy];
    const bVal = b[sortBy];
    let comparison = 0;
    if (typeof aVal === "number" && typeof bVal === "number") {
      comparison = aVal - bVal;
    } else {
      comparison = String(aVal).localeCompare(String(bVal));
    }
    return sortDirection === "asc" ? comparison : -comparison;
  });

  const total = results.length;
  const start = (page - 1) * pageSize;
  const paginated = results.slice(start, start + pageSize);

  return delay({ records: paginated, total, page, pageSize });
}

/**
 * Fetch a single land record by its ID.
 *
 * TODO(FastAPI): Replace with:
 *   const res = await fetch(`${API_BASE_URL}/api/records/${id}`);
 *   if (res.status === 404) return null;
 *   if (!res.ok) throw new Error("Failed to load land record");
 *   return res.json();
 */
export async function getLandRecordById(id: string): Promise<LandRecord | null> {
  const record = landRecords.find((r) => r.id === id) ?? null;
  return delay(record);
}

/**
 * Fetch aggregate dashboard statistics.
 *
 * TODO(FastAPI): Replace with:
 *   const res = await fetch(`${API_BASE_URL}/api/dashboard/stats`);
 *   if (!res.ok) throw new Error("Failed to load dashboard stats");
 *   return res.json();
 */
export async function getDashboardStats(): Promise<DashboardStats> {
  const stats: DashboardStats = {
    totalRecords: landRecords.length,
    verifiedRecords: landRecords.filter((r) => r.status === "Verified").length,
    pendingRecords: landRecords.filter(
      (r) => r.status === "Pending" || r.status === "Under Review"
    ).length,
    documentsUploaded: landRecords.length + recentUploads.length,
  };
  return delay(stats);
}

/**
 * Fetch the most recent document uploads for the dashboard activity feed.
 *
 * TODO(FastAPI): Replace with:
 *   const res = await fetch(`${API_BASE_URL}/api/uploads/recent`);
 *   if (!res.ok) throw new Error("Failed to load recent uploads");
 *   return res.json();
 */
export async function getRecentUploads(): Promise<RecentUpload[]> {
  return delay(recentUploads);
}

export interface UploadDocumentResult {
  success: boolean;
  fileName: string;
  sizeKb: number;
  message: string;
}

/**
 * Upload a document. This mock implementation never contacts a server; it
 * simulates network latency and always resolves successfully so the upload
 * UI can be built and tested end to end.
 *
 * TODO(FastAPI): Replace with a multipart form upload, e.g.:
 *   const formData = new FormData();
 *   formData.append("file", file);
 *   const res = await fetch(`${API_BASE_URL}/api/documents/upload`, {
 *     method: "POST",
 *     body: formData,
 *   });
 *   if (!res.ok) throw new Error("Upload failed");
 *   return res.json();
 *
 * TODO(FastAPI): Consider reporting real upload progress via XHR's
 * `upload.onprogress` or a fetch-based streaming approach, since the plain
 * fetch API does not expose upload progress events.
 */
export async function uploadDocument(file: File): Promise<UploadDocumentResult> {
  return delay(
    {
      success: true,
      fileName: file.name,
      sizeKb: Math.round(file.size / 1024),
      message: "Document received and queued for processing.",
    },
    900
  );
}
