"use client";

import { ChangeEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { LandRecord } from "@/types/landRecord";
import { getLandRecordById } from "@/lib/api";
import {
  ReviewFields,
  FIELD_LABELS,
  toReviewFields,
  overallConfidence,
  isLowConfidence,
  saveReviewFields,
  approveReview,
  rejectReview,
  getReviewDecision,
  ReviewDecisionStatus,
} from "@/lib/reviewData";
import ConfidenceBadge from "@/components/ConfidenceBadge";

type DecisionState = "pending" | ReviewDecisionStatus;

export default function RecordReviewPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;

  const [record, setRecord] = useState<LandRecord | null | undefined>(undefined);
  const [fields, setFields] = useState<ReviewFields | null>(null);
  const [decisionStatus, setDecisionStatus] = useState<DecisionState>("pending");
  const [rejectionReasonSaved, setRejectionReasonSaved] = useState<string | undefined>(
    undefined
  );

  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectionReason, setRejectionReason] = useState("");
  const [rejectionError, setRejectionError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    (async () => {
      const data = await getLandRecordById(id);
      if (!active) return;

      setRecord(data ?? null);
      if (!data) return;

      const existingDecision = getReviewDecision(data.id);
      if (existingDecision) {
        setFields(existingDecision.fields);
        setDecisionStatus(existingDecision.status);
        setRejectionReasonSaved(existingDecision.rejectionReason);
      } else {
        setFields(toReviewFields(data));
      }
    })();

    return () => {
      active = false;
    };
  }, [id]);

  if (record === undefined) {
    return <p className="text-sm text-gray-500">Loading record...</p>;
  }

  if (record === null || !fields) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 text-center shadow-sm">
        <p className="text-sm text-gray-600">No record found for id &ldquo;{id}&rdquo;.</p>
        <Link href="/review" className="mt-4 inline-block text-sm text-blue-700 hover:underline">
          &larr; Back to Review Queue
        </Link>
      </div>
    );
  }

  // Capture as plain, non-null consts so the handlers below don't have to
  // deal with the union type that `record`/`fields` carry as state.
  const currentRecord: LandRecord = record;
  const isDecided = decisionStatus !== "pending";
  const confidence = overallConfidence(fields);

  function handleFieldChange(key: keyof ReviewFields, value: string) {
    setFields((prev) => (prev ? { ...prev, [key]: { ...prev[key], value } } : prev));
    setSaveMessage(null);
  }

  function handleSave() {
    if (!fields) return;
    // Only persists to the in-memory store once a decision exists; before
    // that, edits simply live in local state until Approve/Reject is clicked.
    saveReviewFields(currentRecord.id, fields);
    setSaveMessage("Changes saved");
    setTimeout(() => setSaveMessage(null), 3000);
  }

  function handleApprove() {
    if (!fields) return;
    approveReview(currentRecord.id, fields);
    setDecisionStatus("approved");
    setActionMessage("Record approved successfully.");
  }

  function openRejectModal() {
    setRejectionReason("");
    setRejectionError(null);
    setShowRejectModal(true);
  }

  function handleConfirmReject() {
    if (!rejectionReason.trim()) {
      setRejectionError("A rejection reason is required.");
      return;
    }
    if (!fields) return;
    rejectReview(currentRecord.id, fields, rejectionReason.trim());
    setDecisionStatus("rejected");
    setRejectionReasonSaved(rejectionReason.trim());
    setShowRejectModal(false);
    setActionMessage("Record rejected.");
  }

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <Link href="/review" className="text-sm text-blue-700 hover:underline">
            &larr; Back to Review Queue
          </Link>
          <h2 className="mt-1 text-xl font-semibold text-gray-900">{currentRecord.id}</h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-700">
            {decisionStatus === "pending"
              ? currentRecord.status
              : decisionStatus === "approved"
              ? "Approved"
              : "Rejected"}
          </span>
          <ConfidenceBadge confidence={confidence} />
        </div>
      </div>

      {actionMessage && (
        <div
          className={
            "mb-4 rounded-md border px-4 py-3 text-sm " +
            (decisionStatus === "approved"
              ? "border-green-200 bg-green-50 text-green-800"
              : "border-red-200 bg-red-50 text-red-800")
          }
        >
          <p className="font-medium">{actionMessage}</p>
          {decisionStatus === "rejected" && rejectionReasonSaved && (
            <p className="mt-1 text-red-700">Reason: {rejectionReasonSaved}</p>
          )}
          <Link
            href="/review"
            className="mt-2 inline-block rounded-md bg-white px-3 py-1.5 text-xs font-medium text-gray-700 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
          >
            Back to Review Queue
          </Link>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* LEFT: original document */}
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <h3 className="mb-3 text-sm font-semibold text-gray-900">Original Land Record</h3>

          {/*
            Bhumisetu doesn't currently expose a document URL on LandRecord
            (only documentName/documentType/documentSizeKb), and this
            prototype assumes there's no shared preview component yet.
            If one already exists in the project, swap this placeholder
            block out for it — nothing else on this page depends on it.
          */}
          <div className="flex h-72 flex-col items-center justify-center rounded-md border border-dashed border-gray-300 bg-gray-50 px-4 text-center">
            <svg
              width="40"
              height="40"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              className="text-gray-400"
            >
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <path d="M14 2v6h6" />
            </svg>
            <p className="mt-3 text-sm font-medium text-gray-700">{currentRecord.documentName}</p>
            <p className="text-xs text-gray-500">
              {currentRecord.documentType} &middot;{" "}
              {(currentRecord.documentSizeKb / 1024).toFixed(2)} MB
            </p>
            <p className="mt-2 text-xs text-gray-400">
              Document preview placeholder for this prototype.
            </p>
          </div>
        </div>

        {/* RIGHT: extracted fields */}
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <h3 className="mb-3 text-sm font-semibold text-gray-900">Extracted Fields</h3>

          <div className="space-y-4">
            {FIELD_LABELS.map(({ key, label }) => {
              const field = fields[key];
              const low = isLowConfidence(field.confidence);
              return (
                <div
                  key={key}
                  className={
                    "rounded-md border p-3 " +
                    (low ? "border-amber-300 bg-amber-50" : "border-gray-200")
                  }
                >
                  <label className="mb-1 block text-xs font-medium text-gray-600">{label}</label>
                  <input
                    type="text"
                    value={field.value}
                    disabled={isDecided}
                    onChange={(e: ChangeEvent<HTMLInputElement>) =>
                      handleFieldChange(key, e.target.value)
                    }
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 disabled:bg-gray-100 disabled:text-gray-500"
                  />
                  <div className="mt-1.5 flex items-center justify-between">
                    <span
                      className={
                        "text-xs font-medium " + (low ? "text-amber-700" : "text-gray-500")
                      }
                    >
                      Confidence: {field.confidence.toFixed(2)}
                    </span>
                    {low && (
                      <span className="text-xs font-medium text-amber-700">⚠ Needs review</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {!isDecided && (
            <div className="mt-5 space-y-3">
              <div className="flex flex-wrap items-center gap-3">
                <button
                  onClick={handleSave}
                  className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Save Changes
                </button>
                {saveMessage && (
                  <span className="text-sm font-medium text-green-700">{saveMessage}</span>
                )}
              </div>

              <div className="flex flex-wrap gap-3 border-t border-gray-100 pt-4">
                <button
                  onClick={handleApprove}
                  className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
                >
                  Approve Record
                </button>
                <button
                  onClick={openRejectModal}
                  className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
                >
                  Reject Record
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Reject modal */}
      {showRejectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
          <div className="w-full max-w-md rounded-lg bg-white p-5 shadow-lg">
            <h4 className="text-base font-semibold text-gray-900">Reject Record</h4>
            <p className="mt-1 text-sm text-gray-500">
              Please explain why this record is being rejected. This is required.
            </p>
            <textarea
              value={rejectionReason}
              onChange={(e: ChangeEvent<HTMLTextAreaElement>) => {
                setRejectionReason(e.target.value);
                if (e.target.value.trim()) setRejectionError(null);
              }}
              rows={4}
              placeholder="e.g. Owner name does not match the original document"
              className="mt-3 w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500"
            />
            {rejectionError && <p className="mt-1 text-xs text-red-600">{rejectionError}</p>}
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setShowRejectModal(false)}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmReject}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
