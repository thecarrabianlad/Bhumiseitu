"use client";

import { useRef, useState } from "react";
import { UploadIcon } from "@/components/icons";

const ACCEPTED_TYPES = ["application/pdf", "image/png", "image/jpeg", "image/jpg"];
const ACCEPTED_EXTENSIONS = ".pdf,.png,.jpg,.jpeg";
const MAX_SIZE_MB = 15;

interface UploadDropzoneProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

export default function UploadDropzone({ onFileSelected, disabled }: UploadDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function validateAndEmit(file: File) {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      setError("Unsupported file type. Please upload a PDF, PNG, or JPG file.");
      return;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File is too large. Maximum size is ${MAX_SIZE_MB} MB.`);
      return;
    }
    setError(null);
    onFileSelected(file);
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;
    const file = e.dataTransfer.files?.[0];
    if (file) validateAndEmit(file);
  }

  function handleBrowseChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) validateAndEmit(file);
    e.target.value = "";
  }

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`flex flex-col items-center justify-center rounded-md border-2 border-dashed px-6 py-12 text-center transition-colors ${
          disabled
            ? "cursor-not-allowed border-border bg-canvas opacity-60"
            : isDragging
            ? "border-brand-600 bg-brand-50"
            : "border-border-strong bg-canvas hover:border-brand-400"
        }`}
      >
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-600">
          <UploadIcon className="h-[22px] w-[22px]" />
        </div>
        <p className="mt-4 text-sm font-medium text-ink-900">
          Drag and drop a document here
        </p>
        <p className="mt-1 text-sm text-ink-500">or</p>
        <button
          type="button"
          disabled={disabled}
          onClick={() => inputRef.current?.click()}
          className="mt-3 rounded-md border border-border-strong bg-surface px-4 py-2 text-sm font-medium text-ink-900 hover:bg-canvas disabled:cursor-not-allowed disabled:opacity-60"
        >
          Browse files
        </button>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS}
          className="sr-only"
          onChange={handleBrowseChange}
          disabled={disabled}
        />
        <p className="mt-4 text-xs text-ink-300">
          Supported formats: PDF, PNG, JPG &middot; Maximum size {MAX_SIZE_MB} MB
        </p>
      </div>
      {error && (
        <p role="alert" className="mt-2 text-sm text-status-rejected">
          {error}
        </p>
      )}
    </div>
  );
}
