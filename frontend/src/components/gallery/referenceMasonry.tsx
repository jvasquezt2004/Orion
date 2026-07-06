import { ReferenceMasonryCard } from "./referenceMasonryCard"
import type { Reference } from "#/lib/types"

type ReferenceMasonryProps = {
  references: Array<Reference>
}

export function ReferenceMasonry({ references }: ReferenceMasonryProps) {
  return (
    <div className="columns-1 gap-5 sm:columns-2 md:columns-3 xl:columns-4 2xl:columns-5">
      {references.map((reference, index) => (
        <div key={reference.id} className="mb-5 break-inside-avoid">
          <ReferenceMasonryCard reference={reference} index={index} />
        </div>
      ))}
    </div>
  )
}
