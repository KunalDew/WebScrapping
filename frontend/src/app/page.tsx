"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Link from "next/link";
import { Search, Loader2, Sparkles, BookOpen, Database, BrainCircuit, ArrowRight, LogOut, Download, DollarSign, XCircle } from "lucide-react";
import { useSession, signOut } from "next-auth/react";

export default function Home() {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [status, setStatus] = useState("");
  const [report, setReport] = useState("");
  const [metrics, setMetrics] = useState<any>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const { data: session } = useSession();
  
  const endOfReportRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (report && endOfReportRef.current) {
      endOfReportRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [report]);

  const downloadReport = () => {
    const blob = new Blob([report], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "research_report.md";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    setStatus("Initializing research agent...");
    setReport("");
    setMetrics(null);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://research-api-509516380442.us-central1.run.app";
    const apiKeyParam = session?.backendApiKey ? `&api_key=${encodeURIComponent(session.backendApiKey)}` : "";
    const eventSource = new EventSource(`${apiUrl}/api/research?question=${encodeURIComponent(query)}${apiKeyParam}`);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.status === "Started") {
          setTaskId(data.task_id);
        } else if (data.status === "Complete") {
          setStatus("Research complete!");
          setReport(data.report);
          setMetrics({
            sources: data.sources_used,
            tokens: data.total_tokens_used
          });
          eventSource.close();
          setIsSearching(false);
        } else if (data.status === "Error") {
          setStatus(`Error: ${data.error}`);
          eventSource.close();
          setIsSearching(false);
        } else if (data.status === "Heartbeat") {
          // Ignore keep-alive heartbeats
        } else {
          // Normal progress update: worker sends {"message": "..."}
          setStatus(data.status || data.message || "Working...");
        }
      } catch (err) {
        console.error("Failed to parse SSE message", err);
      }
    };

    eventSource.onerror = (err) => {
      console.error("EventSource failed:", err);
      setStatus("Connection to agent lost.");
      eventSource.close();
      setIsSearching(false);
      setTaskId(null);
    };
  };

  const handleStopRequest = async () => {
    if (!taskId) return;
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://research-api-509516380442.us-central1.run.app";
      const apiKeyParam = session?.backendApiKey ? `?api_key=${encodeURIComponent(session.backendApiKey as string)}` : "";
      
      // Call the backend to revoke the task
      await fetch(`${apiUrl}/api/research/${taskId}/stop${apiKeyParam}`, { method: 'POST' });
      
      // Close the EventSource locally
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      
      setStatus("Research cancelled by user.");
      setIsSearching(false);
      setTaskId(null);
    } catch (err) {
      console.error("Failed to stop request", err);
    }
  };

  return (
    <main className="min-h-screen bg-[#09090b] text-zinc-50 flex flex-col items-center p-6 sm:p-12 md:p-24 selection:bg-blue-500/30">
      
      {/* Navigation */}
      {session && (
        <div className="absolute top-6 right-6 flex items-center space-x-6 z-50">
          <Link href="/history" className="text-zinc-400 hover:text-zinc-100 text-sm font-medium transition-colors">
            History
          </Link>
          <button
            onClick={() => signOut()}
            className="flex items-center space-x-2 text-zinc-400 hover:text-zinc-100 transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span className="text-sm font-medium">Sign Out</span>
          </button>
        </div>
      )}

      {/* Header section transitions up when searching */}
      <div className={`w-full max-w-4xl transition-all duration-700 ease-in-out flex flex-col items-center ${isSearching || report ? "mb-12 mt-0 scale-95" : "my-auto scale-100"}`}>
        
        {!isSearching && !report && (
          <div className="flex items-center space-x-3 mb-6 animate-fade-in-down">
            <div className="p-3 bg-blue-500/10 rounded-2xl border border-blue-500/20 glow-effect">
              <BrainCircuit className="w-8 h-8 text-blue-400" />
            </div>
            <h1 className="text-4xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-zinc-100 to-zinc-500 tracking-tight">
              DeepResearch AI
            </h1>
          </div>
        )}
        
        {!isSearching && !report && (
          <p className="text-zinc-400 text-lg mb-10 text-center max-w-2xl animate-fade-in-up delay-100">
            Enterprise-grade autonomous web research. Ask a question, and the agent will plan, search, scrape, fact-check, and synthesize a comprehensive report.
          </p>
        )}

        <form onSubmit={handleSearch} className="w-full relative group z-10">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-500/20 blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-full pointer-events-none" />
          <div className="relative flex items-center bg-zinc-900 border border-zinc-800 rounded-full p-2 shadow-2xl transition-all duration-300 focus-within:border-blue-500/50 focus-within:ring-2 focus-within:ring-blue-500/20">
            <Search className="w-6 h-6 text-zinc-400 ml-4" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="What do you want to research today?"
              className="flex-1 bg-transparent border-none outline-none text-zinc-100 px-4 py-3 text-lg placeholder:text-zinc-600 w-full"
              disabled={isSearching}
            />
            <button
              type="submit"
              disabled={isSearching || !query.trim()}
              className="bg-zinc-100 text-zinc-900 hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed rounded-full px-6 py-3 font-medium transition-all flex items-center space-x-2"
            >
              <span>{isSearching ? "Researching" : "Search"}</span>
              {isSearching ? <Loader2 className="w-4 h-4 animate-spin ml-2" /> : <ArrowRight className="w-4 h-4 ml-2" />}
            </button>
          </div>
        </form>

        {isSearching && !report && (
          <div className="mt-12 flex flex-col items-center text-center animate-fade-in-up">
            <div className="relative flex items-center justify-center mb-6">
              <div className="absolute inset-0 bg-blue-500/20 rounded-full blur-xl animate-pulse" />
              <div className="relative p-4 bg-zinc-900 border border-zinc-800 rounded-2xl shadow-xl flex items-center justify-center">
                {status.toLowerCase().includes("search") || status.toLowerCase().includes("generat") || status.toLowerCase().includes("filter") ? (
                  <Search className="w-8 h-8 text-blue-400 animate-bounce" />
                ) : status.toLowerCase().includes("scrap") || status.toLowerCase().includes("read") ? (
                  <BookOpen className="w-8 h-8 text-emerald-400 animate-pulse" />
                ) : status.toLowerCase().includes("synth") || status.toLowerCase().includes("think") ? (
                  <BrainCircuit className="w-8 h-8 text-purple-400 animate-pulse" />
                ) : (
                  <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
                )}
              </div>
            </div>
            
            <div className="flex items-center space-x-3 mb-2">
              <Loader2 className="w-4 h-4 text-zinc-400 animate-spin" />
              <p className="text-xl text-zinc-200 font-medium tracking-wide">
                {status}
              </p>
            </div>
            <p className="text-zinc-500 text-sm max-w-md mb-6">
              The agent is autonomously navigating the web. This usually takes 1-2 minutes depending on the complexity of the topic.
            </p>
            {taskId && (
              <button
                onClick={handleStopRequest}
                className="flex items-center space-x-2 text-zinc-400 hover:text-red-400 transition-all px-5 py-2 rounded-full border border-zinc-800 hover:border-red-900/50 hover:bg-red-900/10 active:scale-95"
              >
                <XCircle className="w-4 h-4" />
                <span className="text-sm font-medium">Stop Request</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Report Section */}
      {report && (
        <div className="w-full max-w-4xl bg-zinc-900/50 border border-zinc-800 rounded-3xl p-8 md:p-12 shadow-2xl backdrop-blur-xl animate-fade-in-up">
          
          <div className="flex items-center space-x-4 mb-8 pb-8 border-b border-zinc-800/50">
            <div className="p-2 bg-purple-500/10 rounded-lg">
              <Sparkles className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-zinc-200">Synthesis Complete</h2>
              <p className="text-zinc-500 text-sm">{status}</p>
            </div>
          </div>
          
          <div className="markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {report}
            </ReactMarkdown>
          </div>
          <div ref={endOfReportRef} />

          {/* Metrics Footer */}
          {metrics && (
            <div className="mt-12 pt-8 border-t border-zinc-800/50 flex flex-wrap gap-4 items-center justify-between">
              <div className="flex flex-wrap gap-4">
                <div className="flex items-center space-x-2 bg-zinc-900 border border-zinc-800 rounded-full px-4 py-2 text-sm text-zinc-400">
                  <BookOpen className="w-4 h-4 text-emerald-400" />
                  <span>{metrics.sources} Sources Synthesized</span>
                </div>
                <div className="flex items-center space-x-2 bg-zinc-900 border border-zinc-800 rounded-full px-4 py-2 text-sm text-zinc-400">
                  <Database className="w-4 h-4 text-blue-400" />
                  <span>{metrics.tokens.toLocaleString()} Tokens Processed</span>
                </div>
                <div className="flex items-center space-x-2 bg-zinc-900 border border-zinc-800 rounded-full px-4 py-2 text-sm text-zinc-400">
                  <DollarSign className="w-4 h-4 text-amber-400" />
                  <span>${(metrics.tokens * 0.0000002).toFixed(4)} Cost</span>
                </div>
              </div>
              <button 
                onClick={downloadReport}
                className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white rounded-full px-6 py-2 text-sm font-medium transition-colors shadow-lg shadow-blue-500/20"
              >
                <Download className="w-4 h-4" />
                <span>Download .md</span>
              </button>
            </div>
          )}
        </div>
      )}
      
    </main>
  );
}
