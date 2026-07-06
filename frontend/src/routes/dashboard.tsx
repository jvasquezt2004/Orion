import { createFileRoute } from "@tanstack/react-router"
import { ReferenceMasonry } from "#/components/gallery/referenceMasonry"
import { fetchRegistries } from "#/server-fns/registries"
import type { Reference } from "#/lib/types"

export const Route = createFileRoute("/dashboard")({
  loader: async () => {
    try {
      const references = await fetchRegistries()
      return { references, error: null }
    } catch (err) {
      return {
        references: [] as Array<Reference>,
        error: err instanceof Error ? err.message : "Failed to load",
      }
    }
  },
  component: Dashboard,
})

function Dashboard() {
  const { references, error } = Route.useLoaderData()

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h2 className="font-mono text-sm uppercase text-[#d8cfca]">
            Error loading references
          </h2>
          <p className="mt-2 font-mono text-[0.65rem] uppercase text-[#8d817c]">
            {error}
          </p>
          <p className="mt-4 font-mono text-[0.55rem] uppercase text-[#8d817c]/60">
            Is the backend running on port 8000?
          </p>
        </div>
      </div>
    )
  }

  if (references.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h2 className="font-mono text-sm uppercase text-[#d8cfca]">
            No references yet
          </h2>
          <p className="mt-2 font-mono text-[0.65rem] uppercase text-[#8d817c]">
            Paste an image or URL to get started
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen px-6 py-8 sm:px-8 md:px-12">
      <div className="mb-8">
        <h1 className="font-mono text-[0.65rem] uppercase tracking-[0.2em] text-[#4fb8b2]">
          /{references.length} references
        </h1>
      </div>
      <ReferenceMasonry references={references} />
    </div>
  )
}
