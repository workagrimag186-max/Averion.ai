"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { ChatHistorySidebar } from "@/components/chat-history-sidebar";
import { CitationSourcePanel } from "@/components/citation-source-panel";
import { FeedbackControls } from "@/components/feedback-controls";
import {
  ChatCitation,
  getConversation,
  sendChatMessage,
  transcribeAudio,
} from "@/lib/api";

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
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isLoadingConversation, setIsLoadingConversation] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const canSend = useMemo(
    () => question.trim().length > 0 && !isSending,
    [question, isSending]
  );
  const microphoneAvailable = useMemo(() => {
    return (
      typeof navigator !== "undefined" && !!navigator.mediaDevices?.getUserMedia
    );
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function loadConversation(convId: string) {
    try {
      setIsLoadingConversation(true);
      setErrorMessage(null);

      const response = await getConversation(convId);
      const conversation = response.conversation;

      // Convert messages to ChatMessage format
      const loadedMessages: ChatMessage[] = conversation.messages.map((msg) => ({
        id: msg.id,
        role: msg.role as "user" | "assistant",
        content: msg.content,
        citations: msg.role === "assistant" ? msg.citations : undefined,
      }));

      setMessages(loadedMessages);
      setConversationId(conversation.id);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Failed to load conversation"
      );
    } finally {
      setIsLoadingConversation(false);
    }
  }

  function handleNewChat() {
    setConversationId(null);
    setMessages([]);
    setQuestion("");
    setErrorMessage(null);
  }

  function handleSelectConversation(convId: string) {
    if (convId === conversationId) {
      return; // Already viewing this conversation
    }
    loadConversation(convId);
  }

  async function handleMicClick() {
    if (isRecording) {
      // Stop recording
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
        mediaRecorderRef.current.stop();
      }
      return;
    }

    try {
      setErrorMessage(null);
      
      // Request microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm"
      });
      
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
        
        setIsRecording(false);
        setIsTranscribing(true);
        
        try {
          // Create audio blob
          const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
          
          if (audioBlob.size === 0) {
            setErrorMessage("Recording is empty. Please try again.");
            setIsTranscribing(false);
            return;
          }
          
          // Send to backend for transcription
          const response = await transcribeAudio(audioBlob);
          
          // Set transcript in input field
          setQuestion(response.transcript);
          setIsTranscribing(false);
          
        } catch (error: any) {
          setIsTranscribing(false);
          setErrorMessage(error instanceof Error ? error.message : "Transcription failed. Please try again.");
        }
      };
      
      mediaRecorder.onerror = () => {
        setIsRecording(false);
        setIsTranscribing(false);
        setErrorMessage("Recording failed. Please try again.");
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      
    } catch (error: any) {
      setIsRecording(false);
      
      if (error.name === "NotAllowedError") {
        setErrorMessage("Microphone access denied. Please allow microphone permissions in your browser.");
      } else if (error.name === "NotFoundError") {
        setErrorMessage("No microphone found. Please check your device.");
      } else {
        setErrorMessage("Failed to start recording. Please try again.");
      }
    }
  }

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
    <section className="grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)_320px]">
      <ChatHistorySidebar
        currentConversationId={conversationId}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
      />

      <div className="flex min-h-[560px] flex-col rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-5 py-4">
          <h2 className="text-base font-semibold text-slate-950">Conversation</h2>
          <p className="mt-1 text-sm text-slate-500">
            Ask about uploaded documents and review the returned sources.
          </p>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto p-5">
          {isLoadingConversation ? (
            <div className="space-y-3 rounded-md border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-medium text-slate-700">Loading conversation...</p>
              <div className="space-y-2">
                <div className="h-4 w-3/4 rounded bg-slate-200 animate-pulse" />
                <div className="h-4 w-1/2 rounded bg-slate-200 animate-pulse" />
              </div>
            </div>
          ) : messages.length === 0 ? (
            <div className="rounded-md border border-slate-200 bg-slate-50 p-5">
              <p className="text-sm font-semibold text-slate-800">No messages yet</p>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                Ask a question after uploading a document. Answers will appear here with
                sources and feedback controls.
              </p>
              <p className="mt-3 text-sm font-medium text-slate-700">
                Try: What does the uploaded document say?
              </p>
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

                {message.role === "assistant" ? (
                  <div className="mt-4 space-y-2">
                    <p className="text-xs font-semibold uppercase tracking-normal text-slate-500">
                      Sources
                    </p>
                    <CitationSourcePanel citations={message.citations ?? []} />
                  </div>
                ) : null}

                {message.role === "assistant" ? (
                  <FeedbackControls messageId={message.id} />
                ) : null}
              </div>
            </article>
          ))}

          {isSending ? (
            <div className="space-y-3 rounded-md border border-slate-200 bg-slate-50 p-4" aria-live="polite">
              <p className="text-sm font-medium text-slate-700">Generating answer...</p>
              <div className="space-y-2">
                <div className="h-4 w-3/4 rounded bg-slate-200" />
                <div className="h-4 w-1/2 rounded bg-slate-200" />
              </div>
              <div className="mt-3 space-y-2">
                <p className="text-xs font-semibold uppercase tracking-normal text-slate-500">
                  Sources
                </p>
                <CitationSourcePanel citations={[]} isLoading />
              </div>
            </div>
          ) : null}

          <div ref={messagesEndRef} />

          {errorMessage ? (
            <div className="rounded-md border border-red-200 bg-red-50 p-4" role="alert">
              <p className="text-sm font-semibold text-red-800">Chat request failed</p>
              <p className="mt-1 text-sm leading-6 text-red-700">{errorMessage}</p>
              <button
                className="mt-3 rounded-md border border-red-200 bg-white px-3 py-1.5 text-sm font-medium text-red-700 transition hover:bg-red-100"
                onClick={() => setErrorMessage(null)}
                type="button"
              >
                Dismiss
              </button>
            </div>
          ) : null}
        </div>

        <form className="border-t border-slate-200 p-4" onSubmit={handleSubmit}>
          <label className="sr-only" htmlFor="chat-question">
            Ask a question
          </label>
          <div className="flex flex-col gap-3 sm:flex-row">
            <div className="relative flex-1">
              <textarea
                className="min-h-24 w-full resize-none rounded-md border border-slate-300 bg-white px-3 py-2 pr-12 text-sm leading-6 text-slate-950 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                id="chat-question"
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask a question about your uploaded documents..."
                value={question}
                disabled={isRecording || isTranscribing}
              />
              {microphoneAvailable && (
                <button
                  type="button"
                  onClick={handleMicClick}
                  disabled={isSending || isTranscribing}
                  className={`absolute bottom-2 right-2 rounded-md p-2 transition ${
                    isRecording
                      ? "bg-red-600 text-white hover:bg-red-700"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  } disabled:cursor-not-allowed disabled:opacity-50`}
                  title={isRecording ? "Stop recording" : "Start voice input"}
                >
                  {isRecording ? (
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <rect x="6" y="6" width="12" height="12" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  ) : (
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    </svg>
                  )}
                </button>
              )}
              {isRecording && (
                <div className="absolute left-3 top-2 flex items-center gap-2">
                  <span className="flex h-2 w-2">
                    <span className="absolute inline-flex h-2 w-2 animate-ping rounded-full bg-red-400 opacity-75"></span>
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-red-500"></span>
                  </span>
                  <span className="text-xs font-medium text-red-600">🎤 Recording...</span>
                </div>
              )}
              {isTranscribing && (
                <div className="absolute left-3 top-2 flex items-center gap-2">
                  <span className="flex h-2 w-2">
                    <span className="absolute inline-flex h-2 w-2 animate-ping rounded-full bg-blue-400 opacity-75"></span>
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-blue-500"></span>
                  </span>
                  <span className="text-xs font-medium text-blue-600">⏳ Transcribing...</span>
                </div>
              )}
            </div>
            <button
              className="rounded-md bg-blue-600 px-5 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={!canSend}
              type="submit"
            >
              {isSending ? "Sending..." : "Send"}
            </button>
          </div>
          {!microphoneAvailable && (
            <p className="mt-2 text-xs text-slate-500">
              Voice input not supported in this browser
            </p>
          )}
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

// Made with Bob
