import { createServerFn } from "@tanstack/react-start"
import { z } from "zod"
import { BACKEND_URL } from "#/lib/backend"

const createUrlSchema = z.object({
  originalUrl: z.string().url(),
})

async function extractErrorDetail(res: Response) {
  try {
    const body = (await res.json()) as { detail?: unknown }
    return typeof body.detail === "string" ? body.detail : null
  } catch {
    return null
  }
}

export const createUrl = createServerFn({ method: "POST" })
  .validator(createUrlSchema)
  .handler(async ({ data }) => {
    const res = await fetch(`${BACKEND_URL}/api/urls`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    })

    if (!res.ok) {
      const detail = await extractErrorDetail(res)
      throw new Error(detail ?? `Backend returned ${res.status}`)
    }

    return res.json() as Promise<{ id: string; status: string }>
  })
