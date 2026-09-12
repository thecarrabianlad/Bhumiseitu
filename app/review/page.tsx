"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { LandRecord } from "@/types/landRecord";
import { getLandRecords } from "@/lib/api";
import {
  ReviewFields,
  toReviewFields,
  overallConfidence,
  countLowConfidenceFields,
  isLowConfidence,
  getReviewDecision,
} from "@/lib/reviewData";
import ConfidenceBadge from "@/components/ConfidenceBadge";

type QueueItem = {
  record: LandRecord;
  fields: ReviewFields;
  confidence: number;
};

export default function ReviewQueuePage() {
  const [items, setItems] = useState<QueueItem[] | null>(null);

  useEffect(() => {
    let active = true;

    (async () => {
      const result = await getLandRecords();
if (!active) return;

const allRecords = result.records;
      

      const queueItems: QueueItem[] = allRecords
        // Only records still awaiting a clerk decision belong in the queue.
        .filter((r) => r.status === "Pending" || r.status === "Under Review")
        // Records already decided in this session shouldn't show up again,
        // even though we never mutate the original mock record's status.
        .filter((r) => !getReviewDecision(r.id))
        .map((record) => {
          const fields = toReviewFields(record);
          return { record, fields, confidence: overallConfidence(fields) };
        })
        // Lowest confidence first so clerks see the most urgent records.
        .sort((a, b) => a.confidence - b.confidence);

      setItems(queueItems);
    })();

    return () => {
      active = false;
    };
  }, []);

  if (!items) {
    return <p className="text-sm text-gray-500">Loading review queue...</p>;
  }

  const lowConfidenceCount = items.filter((i) => isLowConfidence(i.confidence)).length;

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Review Queue</h2>
        <p className="text-sm text-gray-500">
          {items.length} records awaiting clerk review &middot; {lowConfidenceCount} need
          attention (below 75% confidence)
        </p>
      </div>

      {items.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-white p-6 text-center text-sm text-gray-500 shadow-sm">
          No pending or under-review records right now.
        </div>
      ) : (
        <>
          {/* Table on larger screens */}
          <div className="hidden overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm md:block">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-xs uppercase tracking-wide text-gray-500">
                <tr>
                  <th className="px-4 py-3">Record ID</th>
                  <th className="px-4 py-3">Owner</th>
                  <th className="px-4 py-3">Village</th>
                  <th className="px-4 py-3">Confidence</th>
                  <th className="px-4 py-3">Low-conf. fields</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {items.map(({ record, fields, confidence }) => {
                  const low = isLowConfidence(confidence);
                  return (
                    <tr key={record.id} className={low ? "bg-amber-50/50" : undefined}>
                      <td className="px-4 py-3 font-medium text-gray-900">{record.id}</td>
                      <td className="px-4 py-3 text-gray-700">{record.ownerName}</td>
                      <td className="px-4 py-3 text-gray-700">{record.village}</td>
                      <td className="px-4 py-3">
                        <ConfidenceBadge confidence={confidence} />
                      </td>
                      <td className="px-4 py-3 text-gray-700">
                        {countLowConfidenceFields(fields)}
                      </td>
                      <td className="px-4 py-3 text-gray-700">{record.status}</td>
                      <td className="px-4 py-3 text-right">
                        <Link
                          href={`/review/${record.id}`}
                          className="rounded-md bg-blue-700 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-800"
                        >
                          Review
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Cards on small screens */}
          <div className="space-y-3 md:hidden">
            {items.map(({ record, fields, confidence }) => {
              const low = isLowConfidence(confidence);
              return (
                <div
                  key={record.id}
                  className={
                    "rounded-lg border bg-white p-4 shadow-sm " +
                    (low ? "border-amber-300" : "border-gray-200")
                  }
                >
                  <div className="mb-2 flex items-center justify-between">
                    <span className="font-medium text-gray-900">{record.id}</span>
                    <span className="text-xs text-gray-500">{record.status}</span>
                  </div>
                  <p className="text-sm text-gray-700">{record.ownerName}</p>
                  <p className="text-sm text-gray-500">{record.village}</p>
                  <div className="mt-3 flex items-center justify-between">
                    <ConfidenceBadge confidence={confidence} />
                    <span className="text-xs text-gray-500">
                      {countLowConfidenceFields(fields)} low-conf. fields
                    </span>
                  </div>
                  <Link
                    href={`/review/${record.id}`}
                    className="mt-3 block rounded-md bg-blue-700 px-3 py-2 text-center text-sm font-medium text-white hover:bg-blue-800"
                  >
                    Review
                  </Link>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
