"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import UploadDropzone from "@/components/UploadDropzone";
import { uploadDocument } from "@/lib/api";
import { CheckCircleIcon, FileTextIcon, ImageIcon, UploadIcon } from "@/components/icons";

type UploadStage = "idle" | "selected" | "uploading" | "success" | "error";

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export default function UploadPage() {
  const [stage, setStage] = useState<UploadStage>("idle");
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const progressTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (progressTimer.current) clearInterval(progressTimer.current);
    };
  }, []);

  function handleFileSelected(selected: File) {
    setFile(selected);
    setStage("selected");
    setErrorMessage(null);
  }

  function handleReset() {
    setFile(null);
    setStage("idle");
    setProgress(0);
    setErrorMessage(null);
  }

  async function handleUpload() {
    if (!file) return;
    setStage("uploading");
    setProgress(8);

    progressTimer.current = setInterval(() => {
      setProgress((prev) => (prev >= 90 ? prev : prev + Math.random() * 12));
    }, 220);

    try {
      // TODO(FastAPI): uploadDocument() currently resolves against mock data.
      // Replace lib/api.ts's implementation with a real multipart request
      // once the FastAPI endpoint is available; this call site can stay the same.
      const result = await uploadDocument(file);
      if (progressTimer.current) clearInterval(progressTimer.current);
      setProgress(100);
      if (result.success) {
        setTimeout(() => setStage("success"), 250);
      } else {
        setStage("error");
        setErrorMessage(result.message || "Upload failed. Please try again.");
      }
    } catch (err) {
      if (progressTimer.current) clearInterval(progressTimer.current);
      setStage("error");
      setErrorMessage("Something went wrong while uploading. Please try again.");
    }
  }

  const FileIcon = file?.type === "application/pdf" ? FileTextIcon : ImageIcon;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h2 className="text-sm font-semibold text-ink-900">Add a record document</h2>
        <p className="mt-1 text-sm text-ink-500">
          Upload a scanned deed, khasra extract, or property photo to attach to a land record.
          Documents are queued for verification after upload.
        </p>
      </div>

      {stage === "success" ? (
        <div className="flex flex-col items-center rounded-md border border-border bg-surface p-10 text-center shadow-card">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-status-verifiedBg text-status-verified">
            <CheckCircleIcon className="h-7 w-7" />
          </div>
          <h3 className="mt-4 text-base font-semibold text-ink-900">Document uploaded</h3>
          <p className="mt-1 max-w-sm text-sm text-ink-500">
            <span className="font-medium text-ink-700">{file?.name}</span> has been received and
            queued for processing. You will see it reflected in Recent Uploads on the dashboard.
          </p>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            <button
              onClick={handleReset}
              className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
            >
              Upload another document
            </button>
            <Link
              href="/records"
              className="rounded-md border border-border-strong bg-surface px-4 py-2 text-sm font-medium text-ink-900 hover:bg-canvas"
            >
              Go to Land Records
            </Link>
          </div>
        </div>
      ) : (
        <div className="space-y-4 rounded-md border border-border bg-surface p-5 shadow-card sm:p-6">
          <UploadDropzone onFileSelected={handleFileSelected} disabled={stage === "uploading"} />

          {file && (
            <div className="rounded-md border border-border bg-canvas p-4">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-surface text-brand-600 ring-1 ring-border">
                  <FileIcon className="h-[18px] w-[18px]" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-ink-900">{file.name}</p>
                  <p className="text-xs text-ink-300">{formatFileSize(file.size)}</p>
                </div>
                {stage === "selected" && (
                  <button
                    onClick={handleReset}
                    className="shrink-0 text-xs font-medium text-ink-500 hover:text-ink-900"
                  >
                    Remove
                  </button>
                )}
              </div>

              {(stage === "uploading" || stage === "error") && (
                <div className="mt-3">
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-border">
                    <div
                      className="h-full rounded-full bg-brand-600 transition-[width] duration-200 ease-out"
                      style={{ width: `${Math.min(progress, 100)}%` }}
                    />
                  </div>
                  <p className="mt-1.5 text-xs text-ink-300">
                    {stage === "uploading" ? `Uploading… ${Math.round(progress)}%` : "Upload failed"}
                  </p>
                </div>
              )}
            </div>
          )}

          {errorMessage && (
            <p role="alert" className="text-sm text-status-rejected">
              {errorMessage}
            </p>
          )}

          <div className="flex justify-end gap-3">
            {stage !== "idle" && stage !== "uploading" && (
              <button
                onClick={handleReset}
                className="rounded-md border border-border-strong bg-surface px-4 py-2 text-sm font-medium text-ink-900 hover:bg-canvas"
              >
                Cancel
              </button>
            )}
            <button
              onClick={handleUpload}
              disabled={!file || stage === "uploading"}
              className="inline-flex items-center gap-2 rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <UploadIcon className="h-4 w-4" />
              {stage === "uploading" ? "Uploading…" : "Upload"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
