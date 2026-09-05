"use client";

import { useState } from "react";
import { UserButton } from "@clerk/nextjs";
import {
  Folder,
  FileText,
  Library,
  Sparkles,
  Settings,
  Paperclip,
  ArrowUp,
} from "lucide-react";

const API_URL = "http://127.0.0.1:8000";

export default function Home() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleAsk() {
    const question = query.trim();

    console.log("[Paperwise] handleAsk fired:", question);

    if (!question || loading) {
      console.log("[Paperwise] Request stopped:", {
        question,
        loading,
      });
      return;
    }

    setLoading(true);
    setAnswer("");
    setError("");

    console.log("[Paperwise] Sending request to:", `${API_URL}/ask`);

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question,
          arxiv_id: null,
        }),
      });

      console.log("[Paperwise] Backend response:", response.status);

      const data = await response.json();

      console.log("[Paperwise] Response data:", data);

      if (!response.ok) {
        throw new Error(data.detail || "Something went wrong.");
      }

      setAnswer(data.answer);
    } catch (err) {
      console.error("[Paperwise] Request failed:", err);

      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Unable to connect to the Paperwise backend.");
      }
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    console.log("[Paperwise] Form submitted");
    handleAsk();
  }

  return (
    <div className="h-screen overflow-hidden bg-[#FAF9F6] text-[#171717]">
      {/* ================= SIDEBAR ================= */}
      <aside className="fixed inset-y-0 left-0 z-20 flex w-[250px] flex-col border-r border-[#E7E5E0] bg-[#F7F6F2] px-5 py-6">
        {/* Logo */}
        <div className="mb-10 px-2">
          <h1 className="text-[22px] font-semibold tracking-[-0.035em]">
            PAPERWISE
          </h1>
        </div>

        {/* Workspace */}
        <div>
          <p className="mb-3 px-2 text-[10px] font-medium uppercase tracking-[0.12em] text-[#99958D]">
            Workspace
          </p>

          <nav className="space-y-1">
            <NavItem
              icon={<Folder size={17} strokeWidth={1.7} />}
              label="Projects"
              active
            />

            <NavItem
              icon={<FileText size={17} strokeWidth={1.7} />}
              label="Drafts"
            />

            <NavItem
              icon={<Library size={17} strokeWidth={1.7} />}
              label="Library"
            />

            <NavItem
              icon={<Sparkles size={17} strokeWidth={1.7} />}
              label="Discover"
            />
          </nav>
        </div>

        {/* Recent */}
        <div className="mt-9">
          <p className="mb-3 px-2 text-[10px] font-medium uppercase tracking-[0.12em] text-[#99958D]">
            Recent
          </p>

          <div className="space-y-1">
            {/* Real projects will appear here from the database */}
          </div>
        </div>

        {/* Bottom */}
        <div className="mt-auto flex items-center justify-between border-t border-[#E7E5E0] px-2 pt-4">
          <button
            type="button"
            className="flex items-center gap-3 rounded-lg py-2 text-sm text-[#73706A] transition hover:text-[#171717]"
          >
            <Settings size={17} strokeWidth={1.7} />

            <span>Settings</span>
          </button>

          <UserButton
            appearance={{
              elements: {
                avatarBox: "h-8 w-8",
              },
            }}
          />
        </div>
      </aside>

      {/* ================= MAIN ================= */}
      <main className="ml-[250px] h-screen overflow-y-auto">
        {/* Hero */}
        <section className="mx-auto flex w-full max-w-[900px] flex-col items-center px-8 pt-[110px]">
          <h2 className="text-center text-[42px] font-medium tracking-[-0.045em]">
            Research, simplified.
          </h2>

          <p className="mt-4 text-center text-[16px] text-[#77736C]">
            Ask questions. Find answers. Grounded in your papers.
          </p>

          {/* Query Box */}
          <form onSubmit={handleSubmit} className="mt-11 w-full">
            <div className="relative rounded-2xl border border-[#DCD9D2] bg-white shadow-[0_2px_10px_rgba(0,0,0,0.025)] transition focus-within:border-[#BDB9B0]">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask anything about your research..."
                disabled={loading}
                className="min-h-[145px] w-full resize-none bg-transparent px-5 pt-5 pb-14 text-[15px] leading-6 outline-none placeholder:text-[#AAA69E] disabled:cursor-wait"
              />

              {/* Query Actions */}
              <div className="absolute bottom-4 left-4 flex items-center gap-4">
                {/* Upload */}
                <button
                  type="button"
                  title="Upload papers"
                  className="text-[#77736C] transition hover:text-[#171717]"
                  onClick={() =>
                    console.log("[Paperwise] Upload clicked")
                  }
                >
                  <Paperclip size={19} strokeWidth={1.7} />
                </button>

                {/* Discover */}
                <button
                  type="button"
                  title="Discover related papers"
                  className="text-[#77736C] transition hover:text-[#171717]"
                  onClick={() =>
                    console.log("[Paperwise] Discover clicked")
                  }
                >
                  <Sparkles size={19} strokeWidth={1.7} />
                </button>
              </div>

              {/* Submit */}
              <button
                type="submit"
                title="Ask question"
                disabled={loading || !query.trim()}
                className="absolute bottom-3.5 right-4 flex h-9 w-9 items-center justify-center rounded-lg bg-[#171717] text-white transition hover:bg-[#333333] disabled:cursor-not-allowed disabled:opacity-40"
              >
                {loading ? (
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                ) : (
                  <ArrowUp size={17} strokeWidth={2} />
                )}
              </button>
            </div>

            <p className="mt-3 text-center text-[11px] text-[#A19D95]">
              Paperwise answers only from your available research sources.
            </p>
          </form>
        </section>

        {/* ================= ANSWER ================= */}
        {(loading || answer || error) && (
          <section className="mx-auto mt-12 w-full max-w-[900px] px-8 pb-20">
            <div className="border-t border-[#E4E1DA] pt-8">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-[14px] font-medium">Answer</h3>

                {loading && (
                  <span className="text-[11px] text-[#99958D]">
                    Searching your research...
                  </span>
                )}
              </div>

              {/* Loading */}
              {loading && (
                <div className="space-y-3">
                  <div className="h-4 w-[90%] animate-pulse rounded bg-[#EDEBE6]" />
                  <div className="h-4 w-[82%] animate-pulse rounded bg-[#EDEBE6]" />
                  <div className="h-4 w-[65%] animate-pulse rounded bg-[#EDEBE6]" />
                </div>
              )}

              {/* Error */}
              {!loading && error && (
                <div className="rounded-xl border border-[#E4D8D5] bg-[#FBF8F6] p-5 text-[14px] leading-6 text-[#6F625D]">
                  {error}
                </div>
              )}

              {/* Answer */}
              {!loading && answer && (
                <div className="rounded-xl border border-[#E4E1DA] bg-white p-6">
                  <p className="whitespace-pre-wrap text-[15px] leading-7 text-[#33312E]">
                    {answer}
                  </p>
                </div>
              )}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

/* ================================================= */
/* Sidebar Navigation Item                           */
/* ================================================= */

function NavItem({
  icon,
  label,
  active = false,
}: {
  icon: React.ReactNode;
  label: string;
  active?: boolean;
}) {
  return (
    <button
      type="button"
      className={`flex w-full items-center gap-3 rounded-lg px-2 py-2 text-[13px] transition ${
        active
          ? "bg-[#E9E7E1] text-[#171717]"
          : "text-[#73706A] hover:bg-[#ECEAE5] hover:text-[#171717]"
      }`}
    >
      {icon}

      <span>{label}</span>
    </button>
  );
}