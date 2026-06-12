"use client";

import { FormEvent, useState } from "react";
import { ThumbsDown, ThumbsUp, X } from "lucide-react";

import {
  FeedbackRating,
  submitFeedback as submitFeedbackRequest
} from "@/lib/api";

type FeedbackControlsProps = {
  messageId: string;
};

export function FeedbackControls({ messageId }: FeedbackControlsProps) {
  const [rating, setRating] = useState<FeedbackRating | null>(null);
  const [correction, setCorrection] = useState("");
  const [state, setState] = useState<
    "idle" | "submitting" | "submitted" | "error"
  >("idle");

  async function submit(nextRating: FeedbackRating, correctionText = "") {
    setState("submitting");
    try {
      await submitFeedbackRequest({
        message_id: messageId,
        rating: nextRating,
        correction_text: correctionText.trim() || null
      });
      setState("submitted");
    } catch {
      setState("error");
    }
  }

  function chooseRating(nextRating: FeedbackRating) {
    setRating(nextRating);
    setState("idle");
    if (nextRating === "up") void submit("up");
  }

  function handleCorrection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submit("down", correction);
  }

  return (
    <div className="relative flex items-center gap-1">
      <button
        aria-label="Mark answer helpful"
        aria-pressed={rating === "up"}
        className={`rounded-md p-2 transition ${
          rating === "up"
            ? "bg-emerald-500/10 text-emerald-400"
            : "text-zinc-600 hover:bg-zinc-800 hover:text-emerald-400"
        }`}
        disabled={state === "submitting"}
        onClick={() => chooseRating("up")}
        type="button"
      >
        <ThumbsUp size={16} />
      </button>
      <button
        aria-label="Mark answer incorrect"
        aria-pressed={rating === "down"}
        className={`rounded-md p-2 transition ${
          rating === "down"
            ? "bg-red-500/10 text-red-400"
            : "text-zinc-600 hover:bg-zinc-800 hover:text-red-400"
        }`}
        disabled={state === "submitting"}
        onClick={() => chooseRating("down")}
        type="button"
      >
        <ThumbsDown size={16} />
      </button>

      {rating === "down" && state !== "submitted" && (
        <form
          className="absolute bottom-11 left-0 z-20 w-72 rounded-md border border-white/10 bg-zinc-900 p-3 shadow-2xl"
          onSubmit={handleCorrection}
        >
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-zinc-300">
              How should this answer improve?
            </p>
            <button
              aria-label="Close feedback"
              className="text-zinc-600 hover:text-white"
              onClick={() => setRating(null)}
              type="button"
            >
              <X size={14} />
            </button>
          </div>
          <textarea
            className="mt-3 min-h-20 w-full resize-none rounded-md border border-white/10 bg-[#0d0d0d] p-2 text-xs text-white outline-none focus:border-blue-500/60"
            onChange={(event) => setCorrection(event.target.value)}
            placeholder="Describe the problem..."
            value={correction}
          />
          <button
            className="mt-2 h-8 w-full rounded-md bg-blue-500 text-xs font-semibold text-white hover:bg-blue-600 disabled:opacity-50"
            disabled={state === "submitting"}
            type="submit"
          >
            {state === "submitting" ? "Sending..." : "Send feedback"}
          </button>
          {state === "error" && (
            <p className="mt-2 text-xs text-red-400">Feedback could not be sent.</p>
          )}
        </form>
      )}
      {state === "submitted" && (
        <span className="ml-1 text-[10px] font-semibold text-emerald-400">
          Feedback saved
        </span>
      )}
    </div>
  );
}
