import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const comingUp = [
  { sprint: "Sprint 2", item: "Sign in, invites, roles and organizations" },
  { sprint: "Sprint 3", item: "Students, guardians, routes, vehicles and drivers" },
  { sprint: "Sprint 4", item: "Driver trip app: boarded, dropped off, absent, location" },
  { sprint: "Sprint 5", item: "Parent WhatsApp messages and the notification log" },
];

export function DashboardPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Foundation build. The school portal becomes this screen once the wireframes are approved and Sprint 2
          adds accounts.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>What lands next</CardTitle>
          <CardDescription>
            The MVP 1 scope, in the order the team is building it.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="flex flex-col divide-y divide-border">
            {comingUp.map((entry) => (
              <li key={entry.sprint} className="flex flex-col gap-1 py-3 sm:flex-row sm:gap-4">
                <span className="w-24 shrink-0 text-sm font-medium text-muted-foreground">
                  {entry.sprint}
                </span>
                <span className="text-sm">{entry.item}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
