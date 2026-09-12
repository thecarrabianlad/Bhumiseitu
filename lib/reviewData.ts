// lib/reviewData.ts
//
// Review-specific mock data for the Human-in-the-Loop Clerk Review feature.
//
// This file deliberately does NOT touch types/landRecord.ts or lib/mockData.ts.
// The existing LandRecord has no confidence scores, so this file adds a
// parallel "review fields" representation with mock confidence values,
// built on top of whatever LandRecord already gives us.

import { LandRecord } from "@/types/landRecord";

export const LOW_CONFIDENCE_THRESHOLD = 0.75;

export type ReviewField = {
  value: string;
  confidence: number;
};

export type ReviewFields = {
  ownerName: ReviewField;
  khasraNumber: ReviewField;
  area: ReviewField;
  village: ReviewField;
  tehsil: ReviewField;
  district: ReviewField;
  landUse: ReviewField;
};

export function isLowConfidence(confidence: number): boolean {
  return confidence < LOW_CONFIDENCE_THRESHOLD;
}

// --- Deterministic mock confidence -----------------------------------------
// Same record id + field name always produces the same score, so the queue
// doesn't jump around on every reload, and some fields land intentionally
// below the 0.75 threshold for the demo.

function hashString(seed: string): number {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = (hash * 31 + seed.charCodeAt(i)) % 1000;
  }
  return hash;
}

function mockConfidence(seed: string): number {
  const hash = hashString(seed);
  // Maps to a 0.30 - 0.99 range so both low- and high-confidence fields occur.
  const value = 0.3 + (hash / 999) * 0.69;
  return Math.round(value * 100) / 100;
}

// LandRecord has no tehsil field yet, so we mock one from a small fixed list.
const MOCK_TEHSILS = ["Dadri", "Jewar", "Bisrakh", "Sadar"];

function mockTehsil(seed: string): string {
  const hash = hashString(seed);
  return MOCK_TEHSILS[hash % MOCK_TEHSILS.length];
}

/** Convert an existing LandRecord into the review fields the clerk UI needs. */
export function toReviewFields(record: LandRecord): ReviewFields {
  return {
    ownerName: {
      value: record.ownerName,
      confidence: mockConfidence(record.id + ":ownerName"),
    },
    khasraNumber: {
      value: record.khasraNumber,
      confidence: mockConfidence(record.id + ":khasraNumber"),
    },
    area: {
      value: `${record.areaValue} ${record.areaUnit}`,
      confidence: mockConfidence(record.id + ":area"),
    },
    village: {
      value: record.village,
      confidence: mockConfidence(record.id + ":village"),
    },
    tehsil: {
      value: mockTehsil(record.id),
      confidence: mockConfidence(record.id + ":tehsil"),
    },
    district: {
      value: record.district,
      confidence: mockConfidence(record.id + ":district"),
    },
    landUse: {
      value: record.landType,
      confidence: mockConfidence(record.id + ":landUse"),
    },
  };
}

export const FIELD_LABELS: { key: keyof ReviewFields; label: string }[] = [
  { key: "ownerName", label: "Owner Name" },
  { key: "khasraNumber", label: "Khasra Number" },
  { key: "area", label: "Area" },
  { key: "village", label: "Village" },
  { key: "tehsil", label: "Tehsil" },
  { key: "district", label: "District" },
  { key: "landUse", label: "Land Use" },
];

/** Overall confidence for a record = average of its review field confidences. */
export function overallConfidence(fields: ReviewFields): number {
  const values = Object.values(fields).map((f) => f.confidence);
  const avg = values.reduce((sum, v) => sum + v, 0) / values.length;
  return Math.round(avg * 100) / 100;
}

export function countLowConfidenceFields(fields: ReviewFields): number {
  return Object.values(fields).filter((f) => isLowConfidence(f.confidence)).length;
}

// ---------------------------------------------------------------------------
// Review decisions (save / approve / reject).
//
// The existing lib/api.ts has no review-decision endpoints, and this file
// intentionally does not add fake functions there. For this MVP, decisions
// are kept in a simple in-memory store here, keyed by record id. It resets
// on page reload — that's expected for a prototype with no backend/database.
//
// TODO: Replace this in-memory store with real FastAPI calls once the
// backend exposes review-decision endpoints, e.g.:
//   PATCH /api/records/:id/review-fields   { fields }
//   PATCH /api/records/:id/approve
//   PATCH /api/records/:id/reject          { reason }
// ---------------------------------------------------------------------------

export type ReviewDecisionStatus = "approved" | "rejected";

export type ReviewDecision = {
  fields: ReviewFields;
  status: ReviewDecisionStatus;
  rejectionReason?: string;
};

const reviewDecisions: Record<string, ReviewDecision> = {};

/** Persist edited field values without changing approve/reject status. */
export function saveReviewFields(id: string, fields: ReviewFields): void {
  // TODO: replace with a FastAPI PATCH call to /api/records/:id/review-fields
  const existing = reviewDecisions[id];
  if (existing) {
    reviewDecisions[id] = { ...existing, fields };
  }
}

export function approveReview(id: string, fields: ReviewFields): void {
  // TODO: replace with a FastAPI PATCH call to /api/records/:id/approve
  reviewDecisions[id] = { fields, status: "approved" };
}

export function rejectReview(id: string, fields: ReviewFields, reason: string): void {
  // TODO: replace with a FastAPI PATCH call to /api/records/:id/reject
  reviewDecisions[id] = { fields, status: "rejected", rejectionReason: reason };
}

export function getReviewDecision(id: string): ReviewDecision | undefined {
  return reviewDecisions[id];
}
