import { createFileRoute } from "@tanstack/react-router"
import { BACKEND_URL } from "#/lib/backend"

export const Route = createFileRoute("/api/upload")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const formData = await request.formData()
        const res = await fetch(`${BACKEND_URL}/api/upload`, {
          method: "POST",
          body: formData,
        })

        return new Response(await res.text(), {
          status: res.status,
          headers: { "Content-Type": "application/json" },
        })
      },
    },
  },
})
