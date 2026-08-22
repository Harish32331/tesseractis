"use client";

import { ChangeEvent, DragEvent, useCallback, useRef, useState } from "react";
import { Button } from "@/components/Button";

interface UploadDropzoneProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
  maxSizeMb?: number;
}

const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];

export function UploadDropzone({ onFileSelected, disabled, maxSizeMb = 8 }: UploadDropzoneProps) {
  const [dragOver, setDragOver] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [clientError, setClientError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      setClientError(null);
      // Client-side pre-check for UX only — the backend independently
      // validates the real bytes regardless of what we say here.
      if (!ACCEPTED_TYPES.includes(file.type)) {
        setClientError("Please choose a JPEG, PNG, or WEBP photo.");
        return;
      }
      if (file.size > maxSizeMb * 1024 * 1024) {
        setClientError(`That file is larger than ${maxSizeMb}MB.`);
        return;
      }
      setPreview(URL.createObjectURL(file));
      onFileSelected(file);
    },
    [onFileSelected, maxSizeMb]
  );

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragOver(false);
    if (disabled) return;
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  }

  function onChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }

  function reset() {
    setPreview(null);
    setClientError(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div>
      {!preview ? (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            if (!disabled) setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          className={`flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-12 text-center transition-colors ${
            dragOver ? "border-[var(--color-uncertainty)] bg-[var(--color-card-raised)]" : "border-[var(--color-border)]"
          } ${disabled ? "opacity-50" : ""}`}
        >
          <p className="font-display text-lg">Drop a photo here</p>
          <p className="text-sm text-[var(--color-muted)]">or</p>
          <Button
            type="button"
            variant="secondary"
            disabled={disabled}
            onClick={() => inputRef.current?.click()}
          >
            Choose a photo
          </Button>
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED_TYPES.join(",")}
            onChange={onChange}
            className="sr-only"
            aria-label="Upload a photo of plastic waste"
            disabled={disabled}
          />
          <p className="text-xs text-[var(--color-faint)]">JPEG, PNG, or WEBP · up to {maxSizeMb}MB</p>
          {clientError && (
            <p role="alert" className="text-sm text-[var(--color-danger)]">
              {clientError}
            </p>
          )}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={preview}
            alt="Selected plastic waste photo, ready to analyze"
            className="max-h-80 rounded-lg border border-[var(--color-border)] object-contain"
          />
          {!disabled && (
            <Button type="button" variant="ghost" onClick={reset}>
              Remove and choose another
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
