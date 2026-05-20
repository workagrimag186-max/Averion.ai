"use client";

import { FormEvent, useMemo, useState } from "react";

import { CitationSourcePanel } from "@/components/citation-source-panel";
import { FeedbackControls } from "@/components/feedback-controls";
import { ChatCitation, sendChatMessage } from "@/lib/api";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: ChatCitation[];
};

export function ChatWorkspace() {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const canSend = useMemo(() => question.trim().length > 0 && !isSending, [question, isSending]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || isSending) {
      return;
    }

    const userMessage: ChatMessage = {
      id: `local-${Date.now()}`,
      role: "user",
      content: trimmedQuestion
    };

    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setIsSending(true);
    setErrorMessage(null);

    try {
      const response = await sendChatMessage({
        conversation_id: conversationId,
        question: trimmedQuestion
      });

      setConversationId(response.conversation_id);
      setMessages((current) => [
        ...current,
        {
          id: response.message_id,
          role: "assistant",
          content: response.answer,
          citations: response.citations
        }
      ]);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Chat request failed.");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
      <div className="flex min-h-[560px] flex-col rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-5 py-4">
          <h2 className="text-base font-semibold text-slate-950">Conversation</h2>
          <p className="mt-1 text-sm text-slate-500">
            Ask about uploaded documents and review the returned sources.
          </p>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto p-5">
          {messages.length === 0 ? (
            <div className="rounded-md bg-slate-50 p-5 text-sm leading-6 text-slate-600">
              Try asking: What does the uploaded document say?
            </div>
          ) : null}

          {messages.map((message) => (
            <article
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              key={message.id}
            >
              <div
                className={`max-w-2xl rounded-lg px-4 py-3 text-sm leading-6 ${
                  message.role === "user"
                    ? "bg-blue-600 text-white"
                    : "border border-slate-200 bg-slate-50 text-slate-800"
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>

                {message.role === "assistant" && message.citations?.length ? (
                  <div className="mt-4 space-y-2">
                    <p className="text-xs font-semibold uppercase tracking-normal text-slate-500">
                      Sources
                    </p>
                    <CitationSourcePanel citations={message.citations} />
                  </div>
                ) : null}

                {message.role === "assistant" ? (
                  <FeedbackControls messageId={message.id} />
                ) : null}
              </div>
            </article>
          ))}

          {isSending ? (
            <div className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
              Generating answer...
            </div>
          ) : null}

          {errorMessage ? (
            <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {errorMessage}
            </div>
          ) : null}
        </div>

        <form className="border-t border-slate-200 p-4" onSubmit={handleSubmit}>
          <label className="sr-only" htmlFor="chat-question">
            Ask a question
          </label>
          <div className="flex flex-col gap-3 sm:flex-row">
            <textarea
              className="min-h-24 flex-1 resize-none rounded-md border border-slate-300 bg-white px-3 py-2 text-sm leading-6 text-slate-950 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              id="chat-question"
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask a question about your uploaded documents..."
              value={question}
            />
            <button
              className="rounded-md bg-blue-600 px-5 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={!canSend}
              type="submit"
            >
              {isSending ? "Sending..." : "Send"}
            </button>
          </div>
        </form>
      </div>

      <aside className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-base font-semibold text-slate-950">Session</h2>
        <dl className="mt-4 space-y-4 text-sm">
          <div>
            <dt className="font-medium text-slate-700">Conversation ID</dt>
            <dd className="mt-1 break-all font-mono text-xs text-slate-500">
              {conversationId ?? "New conversation"}
            </dd>
          </div>
          <div>
            <dt className="font-medium text-slate-700">Messages</dt>
            <dd className="mt-1 text-slate-600">{messages.length}</dd>
          </div>
        </dl>
      </aside>
    </section>
  );
}
