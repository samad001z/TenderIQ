import { ReviewClient } from "./review-client";

/** Server entry — the heavy lifting (SSE, state, modal, drawer) is in the client. */
export default async function ReviewPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <ReviewClient tenderId={id} />;
}
