import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { createClient } from "@/lib/supabase/server";
import { cn } from "@/lib/utils";

const STATUS: Record<string, { label: string; cls: string }> = {
  draft: { label: "Draft", cls: "text-cream-faint border-smoke" },
  submitted: { label: "Submitted", cls: "text-verdict-info border-verdict-info/40 bg-verdict-info/10" },
  under_review: { label: "Under Review", cls: "text-verdict-flag border-verdict-flag/40 bg-verdict-flag/10" },
  evaluated: { label: "Evaluated", cls: "text-verdict-info border-verdict-info/40 bg-verdict-info/10" },
  accepted: { label: "Award", cls: "text-verdict-pass border-verdict-pass/40 bg-verdict-pass/10" },
  rejected: { label: "Rejected", cls: "text-verdict-fail border-verdict-fail/40 bg-verdict-fail/10" },
};

type Bid = {
  id: string;
  status: string;
  submitted_at: string | null;
  created_at: string;
  tenders: { title: string; reference_no: string | null } | null;
};

export default async function SubmissionsPage() {
  const supabase = await createClient();
  const { data } = await supabase
    .from("bids")
    .select("id, status, submitted_at, created_at, tenders(title, reference_no)")
    .order("created_at", { ascending: false });
  const bids = (data ?? []) as unknown as Bid[];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-serif text-[32px] font-medium leading-tight text-cream">My bids</h1>
        <p className="mt-1 text-[14px] text-cream-muted">
          {bids.length} {bids.length === 1 ? "submission" : "submissions"}.
        </p>
      </div>

      <Card className="overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>Tender</TableHead>
              <TableHead>Reference</TableHead>
              <TableHead>Submitted</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {bids.length === 0 && (
              <TableRow className="hover:bg-transparent">
                <TableCell className="py-8 text-center text-cream-muted">No bids yet.</TableCell>
              </TableRow>
            )}
            {bids.map((b) => {
              const s = STATUS[b.status] ?? STATUS.draft;
              const when = b.submitted_at ?? b.created_at;
              return (
                <TableRow key={b.id}>
                  <TableCell className="max-w-md font-medium text-cream">{b.tenders?.title ?? "—"}</TableCell>
                  <TableCell className="font-mono text-[12px] text-cream-muted">
                    {b.tenders?.reference_no ?? "—"}
                  </TableCell>
                  <TableCell className="font-mono text-[12px] tabular-nums text-cream-muted">
                    {when ? new Date(when).toISOString().slice(0, 10) : "—"}
                  </TableCell>
                  <TableCell>
                    <span
                      className={cn(
                        "inline-flex rounded-sm border px-2 py-0.5 font-sans text-[11px] font-semibold uppercase tracking-wide",
                        s.cls,
                      )}
                    >
                      {s.label}
                    </span>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
