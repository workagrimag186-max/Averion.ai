"use client";

import { FormEvent, useState } from "react";

import {
  FeedbackDraft,
  FeedbackRating,
  submitFeedback as submitFeedbackRequest
} from "@/lib/api";

type SubmitState = "idle" | "submitting" | "submitted" | "error";

type FeedbackControlsProps = {
  messageId: string;
};

export function FeedbackControls({ messageId }: FeedbackControlsProps) {
  const [rating, setRating] = useState<FeedbackRating | null>(null);
  const [correctionText, setCorrectionText] = useState("");
  const [submitState, setSubmitState] = useState<SubmitState>("idle");

  async function submitFeedback(nextRating: FeedbackRating, nextCorrectionText = "") {
    setSubmitState("submitting");

    try {
      if (!messageId) {
        throw new Error("Missing message id.");
      }

      const feedback: FeedbackDraft = {
        message_id: messageId,
        rating: nextRating,
        correction_text: nextCorrectionText || null
      };

      await submitFeedbackRequest(feedback);

      setSubmitState("submitted");
    } catch {
      setSubmitState("error");
    }
  }

  function handleRating(nextRating: FeedbackRating) {
    setRating(nextRating);
    setSubmitState("idle");

    if (nextRating === "up") {
      submitFeedback("up");
    }
  }

  function handleCorrectionSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    submitFeedback("down", correctionText.trim());
  }

  return (
    <div className="mt-4 border-t border-slate-200 pt-3">
      <div className="flex flex-wrap items-center gap-2">
        <p className="mr-1 text-xs font-medium text-slate-500">Was this helpful?</p>
        <button
          aria-pressed={rating === "up"}
          className={`rounded-md px-2.5 py-1 text-sm ring-1 ring-inset transition ${
            rating === "up"
              ? "bg-green-50 text-green-700 ring-green-200"
              : "bg-white text-slate-600 ring-slate-200 hover:bg-slate-50"
          }`}
          disabled={submitState === "submitting"}
          onClick={() => handleRating("up")}
          type="button"
        >
          Good
        </button>
        <button
          aria-pressed={rating === "down"}
          className={`rounded-md px-2.5 py-1 text-sm ring-1 ring-inset transition ${
            rating === "down"
              ? "bg-red-50 text-red-700 ring-red-200"
              : "bg-white text-slate-600 ring-slate-200 hover:bg-slate-50"
          }`}
          disabled={submitState === "submitting"}
          onClick={() => handleRating("down")}
          type="button"
        >
          Needs correction
        </button>
      </div>

      {rating === "down" ? (
        <form className="mt-3 space-y-2" onSubmit={handleCorrectionSubmit}>
          <label className="sr-only" htmlFor={`correction-${messageId}`}>
            Correction
          </label>
          <textarea
            className="min-h-20 w-full resize-none rounded-md border border-slate-300 bg-white px-3 py-2 text-sm leading-6 text-slate-950 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            id={`correction-${messageId}`}
            onChange={(event) => {
              setCorrectionText(event.target.value);
              setSubmitState("idle");
            }}
            placeholder="What should the answer say instead?"
            value={correctionText}
          />
          <button
            className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={submitState === "submitting"}
            type="submit"
          >
            {submitState === "submitting" ? "Submitting..." : "Submit correction"}
          </button>
        </form>
      ) : null}

      {submitState === "submitted" ? (
        <div className="mt-2 rounded-md border border-green-200 bg-green-50 px-3 py-2" aria-live="polite">
          <p className="text-xs font-semibold text-green-800">Feedback captured</p>
          <p className="mt-1 text-xs leading-5 text-green-700">
            This response is now available for future review.
          </p>
        </div>
      ) : null}

      {submitState === "error" ? (
        <div className="mt-2 rounded-md border border-red-200 bg-red-50 px-3 py-2" role="alert">
          <p className="text-xs font-semibold text-red-800">Feedback could not be submitted</p>
          <p className="mt-1 text-xs leading-5 text-red-700">
            Check that the API is running, then try again.
          </p>
        </div>
      ) : null}
    </div>
  );
}
