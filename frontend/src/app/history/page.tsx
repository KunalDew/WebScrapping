"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useSession } from "next-auth/react";
import { ArrowLeft, Clock, BookOpen, Database, DollarSign, Loader2, ChevronDown, ChevronUp } from "lucide-react";

export default function HistoryPage() {
  const { data: session, status } = useSession();
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    if (status === "loading") return;
    if (!session?.backendApiKey) {
      setLoading(false);
      return;
    }

    const fetchLogs = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://research-api-509516380442.us-central1.run.app";
        const res = await fetch(`${apiUrl}/api/logs?api_key=${encodeURIComponent(session.backendApiKey as string)}`);
        if (res.ok) {
          const data = await res.json();
          setLogs(data.logs || []);
        }
      } catch (err) {
        console.error("Failed to fetch logs:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchLogs();
  }, [session, status]);

  if (status === "loading" || loading) {
    return (
      <main className="min-h-screen bg-[#09090b] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#09090b] text-zinc-50 p-6 sm:p-12 md:p-24 selection:bg-blue-500/30">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-12">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-blue-500/10 rounded-2xl border border-blue-500/20">
              <Clock className="w-8 h-8 text-blue-400" />
            </div>
            <h1 className="text-3xl md:text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-zinc-100 to-zinc-500 tracking-tight">
              Research History
            </h1>
          </div>
          <Link href="/" className="flex items-center space-x-2 text-zinc-400 hover:text-zinc-100 transition-colors">
            <ArrowLeft className="w-5 h-5" />
            <span className="text-sm font-medium">Back to Search</span>
          </Link>
        </div>

        {logs.length === 0 ? (
          <div className="text-center text-zinc-500 mt-20">
            <p>No past researches found.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {logs.map((log) => (
              <div key={log._id} className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6 shadow-xl overflow-hidden transition-all duration-300">
                <div 
                  className="flex justify-between items-center cursor-pointer"
                  onClick={() => setExpandedId(expandedId === log._id ? null : log._id)}
                >
                  <div className="flex-1 pr-6">
                    <h3 className="text-lg font-medium text-zinc-200 line-clamp-1">{log.question}</h3>
                    <p className="text-sm text-zinc-500 mt-1">
                      {new Date(log.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="hidden sm:flex items-center space-x-4 text-xs text-zinc-400">
                      <div className="flex items-center">
                        <BookOpen className="w-3 h-3 mr-1" /> {log.sources_used}
                      </div>
                      <div className="flex items-center">
                        <Database className="w-3 h-3 mr-1" /> {log.total_tokens_used?.toLocaleString()}
                      </div>
                      <div className="flex items-center">
                        <DollarSign className="w-3 h-3 mr-1" /> ${(log.total_tokens_used * 0.0000002).toFixed(4)}
                      </div>
                    </div>
                    {expandedId === log._id ? (
                      <ChevronUp className="w-5 h-5 text-zinc-500" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-zinc-500" />
                    )}
                  </div>
                </div>

                {expandedId === log._id && (
                  <div className="mt-8 pt-8 border-t border-zinc-800/50 animate-fade-in-down">
                    <div className="markdown-body">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {log.report}
                      </ReactMarkdown>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
