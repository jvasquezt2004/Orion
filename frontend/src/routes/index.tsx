import { createFileRoute, Link } from "@tanstack/react-router"

export const Route = createFileRoute("/")({ component: Home })

function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="font-mono text-[0.65rem] uppercase tracking-[0.2em] text-[#4fb8b2]">
          /Orion
        </h1>
        <h2 className="mt-4 text-2xl font-medium text-[#d7ece8]">
          Visual Reference Manager
        </h2>
        <p className="mt-3 font-mono text-[0.65rem] uppercase text-[#afcdc8]">
          Paste images, videos, or URLs to organize your visual references
        </p>
        <Link
          to="/dashboard"
          className="mt-8 inline-block rounded-2xl border border-white/10 bg-[#0f1a1e]/92 px-6 py-3 font-mono text-[0.65rem] uppercase text-[#d7ece8] transition duration-300 hover:border-[#4fb8b2]/80"
        >
          Open Dashboard
        </Link>
      </div>
    </div>
  )
}
