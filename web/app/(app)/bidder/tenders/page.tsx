import Link from "next/link";

import { EvalPill } from "@/components/bidder/eval-pill";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { daysUntil, formatINR } from "@/lib/format";
import { createClient } from "@/lib/supabase/server";
import { cn } from "@/lib/utils";

type Row = {
  id: string;
  title: string;
  ministry: string | null;
  estimated_value: number | null;
  closing_at: string | null;
  parsed_schema: { evaluation_method?: string } | null;
};

function Deadline({ closing }: { closing: string | null }) {
  const d = daysUntil(closing);
  if (d == null) return <span className="text-cream-faint">—</span>;
  if (d <= 0) return <span className="font-mono text-[12px] text-cream-faint">closed</span>;
  return (
    <span className={cn("font-mono text-[12px] tabular-nums", d < 7 ? "text-gold" : "text-cream-muted")}>
      {d}d left
    </span>
  );
}

export default async function BidderTendersPage() {
  const supabase = await createClient();
  const { data } = await supabase
    .from("tenders")
    .select("id, title, ministry, estimated_value, closing_at, parsed_schema")
    .eq("status", "published")
    .order("closing_at", { ascending: true });
  const tenders = (data ?? []) as Row[];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-serif text-[32px] font-medium leading-tight text-cream">Tenders</h1>
        <p className="mt-1 text-[14px] text-cream-muted">
          {tenders.length} published {tenders.length === 1 ? "tender" : "tenders"} open for bidding.
        </p>
      </div>

      <Card className="overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>Title</TableHead>
              <TableHead>Ministry</TableHead>
              <TableHead className="text-right">Value</TableHead>
              <TableHead className="text-right">Deadline</TableHead>
              <TableHead>Method</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tenders.length === 0 && (
              <TableRow className="hover:bg-transparent">
                <TableCell className="py-8 text-center text-cream-muted">
                  No published tenders yet.
                </TableCell>
              </TableRow>
            )}
            {tenders.map((t) => (
              <TableRow key={t.id}>
                <TableCell className="max-w-md">
                  <Link href={`/bidder/tenders/${t.id}`} className="font-medium text-cream hover:text-gold">
                    {t.title}
                  </Link>
                </TableCell>
                <TableCell className="text-cream-muted">{t.ministry ?? "—"}</TableCell>
                <TableCell className="text-right font-mono tabular-nums">
                  {formatINR(t.estimated_value)}
                </TableCell>
                <TableCell className="text-right">
                  <Deadline closing={t.closing_at} />
                </TableCell>
                <TableCell>
                  <EvalPill method={t.parsed_schema?.evaluation_method} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
