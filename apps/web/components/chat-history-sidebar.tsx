"use client";

import { useEffect, useState } from "react";
import {
  ConversationSummary,
  deleteConversation,
  listConversations,
} from "@/lib/api";

type ChatHistorySidebarProps = {
  currentConversationId: string | null;
  onSelectConversation: (conversationId: string) => void;
  onNewChat: () => void;
};

export function ChatHistorySidebar({
  currentConversationId,
  onSelectConversation,
  onNewChat,
}: ChatHistorySidebarProps) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [deleteErrorMessage, setDeleteErrorMessage] = useState<string | null>(
    null
  );

  useEffect(() => {
    loadConversations();
  }, []);

  async function loadConversations() {
    try {
      setIsLoading(true);
      setErrorMessage(null);
      const response = await listConversations();
      setConversations(response.conversations);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Failed to load conversations"
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function handleDelete(conversationId: string, event: React.MouseEvent) {
    event.stopPropagation();

    if (!confirm("Delete this conversation? This cannot be undone.")) {
      return;
    }

    try {
      setDeleteErrorMessage(null);
      await deleteConversation(conversationId);
      setConversations((prev) =>
        prev.filter((conv) => conv.id !== conversationId)
      );

      // If deleting current conversation, start new chat
      if (conversationId === currentConversationId) {
        onNewChat();
      }
    } catch (error) {
      setDeleteErrorMessage(
        error instanceof Error ? error.message : "Failed to delete conversation"
      );
    }
  }

  function groupConversationsByDate(conversations: ConversationSummary[]) {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const lastWeek = new Date(today);
    lastWeek.setDate(lastWeek.getDate() - 7);

    const groups: Record<string, ConversationSummary[]> = {
      Today: [],
      Yesterday: [],
      "Last Week": [],
      Older: [],
    };

    conversations.forEach((conv) => {
      const convDate = new Date(conv.updated_at);
      const convDateOnly = new Date(
        convDate.getFullYear(),
        convDate.getMonth(),
        convDate.getDate()
      );

      if (convDateOnly.getTime() === today.getTime()) {
        groups.Today.push(conv);
      } else if (convDateOnly.getTime() === yesterday.getTime()) {
        groups.Yesterday.push(conv);
      } else if (convDateOnly >= lastWeek) {
        groups["Last Week"].push(conv);
      } else {
        groups.Older.push(conv);
      }
    });

    return groups;
  }

  const groupedConversations = groupConversationsByDate(conversations);

  return (
    <aside className="flex h-full flex-col rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-950">Chat History</h2>
          <button
            onClick={onNewChat}
            className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-blue-700"
            type="button"
          >
            New Chat
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        {deleteErrorMessage && (
          <div className="mb-3 rounded-md border border-red-200 bg-red-50 p-3">
            <p className="text-sm text-red-800">{deleteErrorMessage}</p>
          </div>
        )}

        {isLoading ? (
          <div className="space-y-2">
            <div className="h-12 animate-pulse rounded-md bg-slate-100" />
            <div className="h-12 animate-pulse rounded-md bg-slate-100" />
            <div className="h-12 animate-pulse rounded-md bg-slate-100" />
          </div>
        ) : errorMessage ? (
          <div className="rounded-md border border-red-200 bg-red-50 p-3">
            <p className="text-sm text-red-800">{errorMessage}</p>
            <button
              onClick={loadConversations}
              className="mt-2 text-sm font-medium text-red-700 hover:text-red-800"
              type="button"
            >
              Try again
            </button>
          </div>
        ) : conversations.length === 0 ? (
          <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm text-slate-600">No conversations yet</p>
            <p className="mt-1 text-xs text-slate-500">
              Start a new chat to begin
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {Object.entries(groupedConversations).map(([group, convs]) =>
              convs.length > 0 ? (
                <div key={group}>
                  <h3 className="mb-2 px-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    {group}
                  </h3>
                  <div className="space-y-1">
                    {convs.map((conv) => (
                      <div
                        key={conv.id}
                        className={`group flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm transition cursor-pointer ${
                          conv.id === currentConversationId
                            ? "bg-blue-50 text-blue-900"
                            : "text-slate-700 hover:bg-slate-50"
                        }`}
                        onClick={() => onSelectConversation(conv.id)}
                      >
                        <div className="min-w-0 flex-1">
                          <p className="truncate font-medium">{conv.title}</p>
                          <p className="mt-0.5 text-xs text-slate-500">
                            {conv.message_count} message
                            {conv.message_count !== 1 ? "s" : ""}
                          </p>
                        </div>
                        <button
                          onClick={(e) => handleDelete(conv.id, e)}
                          className="ml-2 rounded p-1 text-slate-400 opacity-0 transition hover:bg-red-50 hover:text-red-600 group-hover:opacity-100"
                          type="button"
                          title="Delete conversation"
                        >
                          <svg
                            className="h-4 w-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                            />
                          </svg>
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null
            )}
          </div>
        )}
      </div>
    </aside>
  );
}
