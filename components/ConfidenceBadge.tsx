// components/ConfidenceBadge.tsx
//
// NOTE: Only add this file if components/ConfidenceBadge.tsx does not
// already exist in the project. If it already exists, check that it reads
// the threshold from lib/reviewData.ts (not a hardcoded number) and reuse it
// instead of adding a second copy.

import { LOW_CONFIDENCE_THRESHOLD, isLowConfidence } from "@/lib/reviewData";

export default function ConfidenceBadge({ confidence }: { confidence: number }) {
  const low = isLowConfidence(confidence);
  const percent = Math.round(confidence * 100);

  return (
    <span
      className={
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium " +
        (low ? "bg-amber-100 text-amber-800" : "bg-green-100 text-green-800")
      }
      title={`Threshold: ${LOW_CONFIDENCE_THRESHOLD}`}
    >
      {low ? "Low" : "High"} confidence &middot; {percent}%
    </span>
  );
}
