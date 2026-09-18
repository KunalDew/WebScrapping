"use client";

import { signIn } from "next-auth/react";
import { useState } from "react";
import { BrainCircuit, Loader2, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    const res = await signIn("credentials", {
      username,
      password,
      redirect: false,
    });

    if (res?.error) {
      setError("Invalid username or password");
      setIsLoading(false);
    } else {
      router.push("/");
      router.refresh();
    }
  };

  return (
    <main className="min-h-screen bg-[#09090b] text-zinc-50 flex flex-col items-center justify-center p-6 selection:bg-blue-500/30">
      <div className="w-full max-w-md bg-zinc-900/50 border border-zinc-800 rounded-3xl p-8 md:p-12 shadow-2xl backdrop-blur-xl animate-fade-in-up">
        
        <div className="flex flex-col items-center mb-8">
          <div className="p-3 bg-blue-500/10 rounded-2xl border border-blue-500/20 glow-effect mb-4">
            <BrainCircuit className="w-8 h-8 text-blue-400" />
          </div>
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-zinc-100 to-zinc-500">
            Secure Access
          </h1>
          <p className="text-zinc-500 text-sm mt-2">Sign in to DeepResearch AI</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-zinc-400 mb-2">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-3 text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-all"
              placeholder="testuser"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-400 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-3 text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-all"
              placeholder="••••••••"
              required
            />
          </div>

          {error && (
            <p className="text-red-400 text-sm text-center">{error}</p>
          )}

          <button
            type="submit"
            disabled={isLoading || !username || !password}
            className="w-full bg-zinc-100 text-zinc-900 hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed rounded-xl px-6 py-3 font-medium transition-all flex items-center justify-center space-x-2 group"
          >
            <span>{isLoading ? "Authenticating..." : "Sign In"}</span>
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin ml-2" />
            ) : (
              <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
            )}
          </button>
        </form>
      </div>
    </main>
  );
}
