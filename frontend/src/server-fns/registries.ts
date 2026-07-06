import { createServerFn } from "@tanstack/react-start"
import { BACKEND_URL } from "#/lib/backend"
import type { Reference } from "#/lib/types"

export const fetchRegistries = createServerFn({ method: "GET" }).handler(
  async (): Promise<Array<Reference>> => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/registries`)
      if (!res.ok) {
        throw new Error(`Backend returned ${res.status}`)
      }
      return await res.json()
    } catch (err) {
      console.error("[fetchRegistries] Error:", err)
      throw err
    }
  }
)
