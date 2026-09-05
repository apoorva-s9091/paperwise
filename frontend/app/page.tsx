"use client";

import { useState, useRef, type FormEvent, type ChangeEvent } from "react";
import { UserButton } from "@clerk/nextjs";
import {
  Folder,
  FileText,
  Library,
  Sparkles,
  Settings,
  Paperclip,
  ArrowUp,
  X,
} from "lucide-react";

const API_URL = "http://127.0.0.1:8000";

export default function Home() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // The paper currently scoping questions -- null means "ask across all papers"
  const [activePaper, setActivePaper] = useState<{ id: string; name: string } | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleUploadClick() {
    fileInputRef.current?.click();
  }

  async function handleFileSelected(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_URL}/papers/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(data?.detail || "Upload failed.");
      }

      setActivePaper({ id: data.paper_id, name: file.name });
      setAnswer("");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to upload the file.",
      );
    } finally {
      setUploading(false);
      // reset the input so selecting the same file again still fires onChange
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  function clearActivePaper() {
    setActivePaper(null);
    setAnswer("");
  }

  async function handleAsk() {
    const question = query.trim();

    if (!question || loading) {
      return;
    }

    setLoading(true);
    setError("");
    setAnswer("");

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question,
          // scope to the uploaded paper if one is active, otherwise
          // search across everything
          paper_id: activePaper?.id ?? null,
          arxiv_id: null,
        }),
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(data?.detail || "Unable to get an answer right now.");
      }

      if (typeof data?.answer !== "string") {
        throw new Error("The server returned an invalid answer.");
      }

      setAnswer(data.answer);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to connect to the Paperwise backend.",
      );
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    void handleAsk();
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

            {/* Real recent projects will be loaded from the database */}

          </div>

        </div>


        {/* Bottom Navigation */}
        <div className="mt-auto flex items-center justify-between border-t border-[#E7E5E0] px-2 pt-4">

          <button
            type="button"
            className="flex items-center gap-3 rounded-lg py-2 text-sm text-[#73706A] transition hover:text-[#171717]"
          >
            <Settings
              size={17}
              strokeWidth={1.7}
            />

            <span>
              Settings
            </span>
          </button>


          {/* Clerk Profile */}
          <UserButton
            appearance={{
              elements: {
                avatarBox: "h-8 w-8",
              },
            }}
          />

        </div>

      </aside>


      {/* ================= MAIN CONTENT ================= */}
      <main className="ml-[250px] h-screen overflow-y-auto">

        {/* Hero */}
        <section className="mx-auto flex w-full max-w-[900px] flex-col items-center px-8 pt-[110px]">

          <h2 className="text-center text-[42px] font-medium tracking-[-0.045em]">
            Research, simplified.
          </h2>

          <p className="mt-4 text-center text-[16px] text-[#77736C]">
            Ask questions. Find answers. Grounded in your papers.
          </p>

          {/* Active paper badge -- shows what questions are currently scoped to */}
          {activePaper && (
            <div className="mt-6 flex items-center gap-2 rounded-full border border-[#DCD9D2] bg-white px-4 py-2 text-[13px] text-[#171717]">
              <FileText size={14} strokeWidth={1.7} />
              <span className="max-w-[300px] truncate">{activePaper.name}</span>
              <button
                type="button"
                onClick={clearActivePaper}
                title="Stop scoping to this paper"
                className="ml-1 text-[#99958D] transition hover:text-[#171717]"
              >
                <X size={14} strokeWidth={2} />
              </button>
            </div>
          )}


          {/* Query Box */}
          <form className="mt-11 w-full" onSubmit={handleSubmit}>

            <div className="relative rounded-2xl border border-[#DCD9D2] bg-white shadow-[0_2px_10px_rgba(0,0,0,0.025)] transition focus-within:border-[#BDB9B0]">

              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={
                  activePaper
                    ? `Ask something about ${activePaper.name}...`
                    : "Ask anything about your research..."
                }
                className="min-h-[145px] w-full resize-none bg-transparent px-5 pt-5 pb-14 text-[15px] leading-6 outline-none placeholder:text-[#AAA69E]"
              />

              {/* Hidden file input, triggered by the paperclip button */}
              <input
                ref={fileInputRef}
                type="file"
                accept="application/pdf"
                hidden
                onChange={handleFileSelected}
              />

              {/* Query Actions */}
              <div className="absolute bottom-4 left-4 flex items-center gap-4">

                {/* Upload Papers */}
                <button
                  type="button"
                  title="Upload a paper"
                  onClick={handleUploadClick}
                  disabled={uploading}
                  className="text-[#77736C] transition hover:text-[#171717] disabled:opacity-50"
                >
                  <Paperclip
                    size={19}
                    strokeWidth={1.7}
                  />
                </button>


                {/* Discover Related Papers */}
                <button
                  type="button"
                  title="Discover related papers"
                  className="text-[#77736C] transition hover:text-[#171717]"
                >
                  <Sparkles
                    size={19}
                    strokeWidth={1.7}
                  />
                </button>

              </div>


              {/* Submit */}
              <button
                type="submit"
                title="Ask question"
                disabled={loading || !query.trim()}
                className="absolute bottom-3.5 right-4 flex h-9 w-9 items-center justify-center rounded-lg bg-[#171717] text-white transition hover:bg-[#333333] disabled:cursor-not-allowed disabled:opacity-50"
              >
                <ArrowUp
                  size={17}
                  strokeWidth={2}
                />
              </button>

            </div>


            <p className="mt-3 text-center text-[11px] text-[#A19D95]">
              {activePaper
                ? `Answering only from "${activePaper.name}".`
                : "Paperwise answers only from your available research sources."}
            </p>

            {uploading && (
              <p className="mt-3 text-center text-[13px] text-[#77736C]">
                Uploading and processing your paper -- this can take a minute...
              </p>
            )}

            {(loading || error || answer) && (
              <section className="mt-8 rounded-2xl border border-[#DCD9D2] bg-white px-5 py-5 shadow-[0_2px_10px_rgba(0,0,0,0.025)]">
                <h3 className="text-[14px] font-medium">Answer</h3>
                {loading && (
                  <p className="mt-3 text-[15px] text-[#77736C]">Thinking...</p>
                )}
                {error && (
                  <p className="mt-3 text-[15px] text-red-600">{error}</p>
                )}
                {answer && (
                  <p className="mt-3 whitespace-pre-wrap text-[15px] leading-6 text-[#171717]">
                    {answer}
                  </p>
                )}
              </section>
            )}

          </form>

        </section>


        {/* ================= RECENT PROJECTS ================= */}
        <section className="mx-auto mt-20 w-full max-w-[900px] px-8 pb-20">

          <div className="mb-5 flex items-center justify-between">

            <h3 className="text-[14px] font-medium">
              Recent projects
            </h3>

            <button
              type="button"
              className="text-[12px] text-[#77736C] transition hover:text-[#171717]"
            >
              View all
            </button>

          </div>


          {/* Projects will be loaded from the database */}

          <div className="rounded-xl border border-dashed border-[#DEDAD2] bg-transparent px-6 py-10 text-center">

            <p className="text-[13px] text-[#99958D]">
              Your recent research projects will appear here.
            </p>

          </div>

        </section>

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

      <span>
        {label}
      </span>

    </button>
  );
}
