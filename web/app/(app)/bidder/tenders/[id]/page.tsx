import { notFound } from "next/navigation";

import { TenderDetail } from "@/components/bidder/tender-detail";
import { createClient } from "@/lib/supabase/server";
import type { TenderSchema } from "@/lib/tender-schema";

export default async function TenderDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createClient();
  const { data } = await supabase
    .from("tenders")
    .select("id, title, ministry, reference_no, estimated_value, status, parsed_schema")
    .eq("id", id)
    .limit(1);
  const tender = data?.[0];
  if (!tender || tender.status !== "published") notFound();

  return (
    <TenderDetail
      tenderId={tender.id}
      meta={{
        title: tender.title,
        ministry: tender.ministry,
        reference_no: tender.reference_no,
        estimated_value: tender.estimated_value,
      }}
      schema={(tender.parsed_schema as TenderSchema) ?? null}
    />
  );
}
