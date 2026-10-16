import { useMutation } from "@tanstack/react-query";
import { useState, type ChangeEvent } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorText } from "@/components/ui/feedback";
import { Label } from "@/components/ui/label";
import { previewRosterImport, runRosterImport, type RosterImportSummary } from "@/lib/api";
import { useSchoolMutation } from "@/lib/school-queries";

// Must match the column names in backend/app/services/roster_import.py.
const TEMPLATE = [
  "first_name,last_name,class,guardian_name,guardian_whatsapp,guardian_relationship," +
    "second_guardian_name,second_guardian_whatsapp,second_guardian_relationship," +
    "route_code,pickup_stop,dropoff_stop",
  "Wanjiru,Otieno,Grade 4,Achieng Otieno,0700 000 001,mother,Otieno Senior,0700 000 002,father,R1,Main gate,Main gate",
  "Baraka,Otieno,Grade 2,Achieng Otieno,0700 000 001,mother,,,,R1,Main gate,",
].join("\r\n");

const TEMPLATE_URL = `data:text/csv;charset=utf-8,${encodeURIComponent(TEMPLATE + "\r\n")}`;

/** Import a roster: preview every row first, then import all or nothing (S3-11). */
export function ImportRoster({ onDone }: { onDone: () => void }) {
  const [fileName, setFileName] = useState("");
  const [text, setText] = useState("");
  const preview = useMutation({ mutationFn: previewRosterImport });
  const run = useSchoolMutation(runRosterImport);

  async function onFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    run.reset();
    if (!file) {
      setText("");
      setFileName("");
      preview.reset();
      return;
    }
    const content = await file.text();
    setFileName(file.name);
    setText(content);
    preview.mutate(content);
  }

  const summary: RosterImportSummary | undefined = run.data ?? preview.data;
  const clean = summary !== undefined && summary.problems.length === 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Import from a spreadsheet</CardTitle>
        <CardDescription>
          Fill in the template (one row per child), save it as CSV, and choose it below. Nothing is saved
          until you press Import, and nothing at all if any row has a problem. Children already here are
          skipped, so you can import a corrected file again.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <a href={TEMPLATE_URL} download="tafi-roster-template.csv" className="text-sm font-semibold underline">
          Download the template
        </a>
        <ul className="list-disc pl-5 text-xs text-muted-foreground">
          <li>Required: first_name, last_name, guardian_name, guardian_whatsapp.</li>
          <li>Numbers like 0712 345 678 are fine. Relationship: mother, father, guardian or other.</li>
          <li>route_code and stop names must match a route and its stops on the Routes &amp; crew page.</li>
          <li>In Excel: File → Save As → “CSV UTF-8”.</li>
        </ul>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="roster-file">Spreadsheet (CSV)</Label>
          <input
            id="roster-file"
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => void onFile(event)}
            className="text-sm file:mr-3 file:rounded-md file:border-0 file:bg-secondary file:px-3 file:py-2 file:text-sm file:font-medium"
          />
        </div>

        {preview.isPending ? <p role="status" className="text-sm text-muted-foreground">Checking {fileName}…</p> : null}
        <ErrorText error={preview.error} fallback="Could not read that file." />

        {summary ? (
          <div role="status" className="flex flex-col gap-3 rounded-xl bg-muted p-4 text-sm">
            <p className="font-semibold">
              {summary.imported ? "Imported." : `${fileName}: ${summary.rows} row${summary.rows === 1 ? "" : "s"} checked.`}
            </p>
            <ul className="grid gap-1 sm:grid-cols-2">
              <li>{summary.children_to_add} children {summary.imported ? "added" : "to add"}</li>
              <li>{summary.children_skipped} already here (skipped)</li>
              <li>
                {summary.guardians_new} new guardian{summary.guardians_new === 1 ? "" : "s"}, {summary.guardians_existing}{" "}
                already known
              </li>
              <li>{summary.assigned_to_routes} put on a route</li>
            </ul>
            {summary.problems.length > 0 ? (
              <div>
                <Badge tone="danger">
                  {summary.problems.length} row{summary.problems.length === 1 ? "" : "s"} to fix
                </Badge>
                <div className="mt-2 max-h-64 overflow-auto rounded-md border border-border bg-card">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-border text-muted-foreground">
                        <th scope="col" className="px-3 py-2 font-medium">Row</th>
                        <th scope="col" className="px-3 py-2 font-medium">Problem</th>
                      </tr>
                    </thead>
                    <tbody>
                      {summary.problems.map((problem) => (
                        <tr key={`${problem.row}-${problem.message}`} className="border-b border-border/60 last:border-0">
                          <td className="px-3 py-2 font-mono">{problem.row}</td>
                          <td className="px-3 py-2">{problem.message}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="mt-2 text-xs text-muted-foreground">
                  Fix these rows in the spreadsheet, save it again and choose the file again.
                </p>
              </div>
            ) : null}
          </div>
        ) : null}

        <ErrorText error={run.error} />
        <div className="flex gap-2">
          {summary?.imported ? (
            <Button onClick={onDone}>Done</Button>
          ) : (
            <Button
              onClick={() => run.mutate(text)}
              disabled={!clean || run.isPending || summary?.children_to_add === 0}
            >
              {run.isPending ? "Importing…" : `Import ${summary?.children_to_add ?? ""} children`}
            </Button>
          )}
          <Button variant="ghost" onClick={onDone}>
            {summary?.imported ? "Close" : "Cancel"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
