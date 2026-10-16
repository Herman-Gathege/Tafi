import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorText, Eyebrow, Loading } from "@/components/ui/feedback";
import { listTodayTrips, startTrip, type TripSummary } from "@/lib/api";
import { useSession } from "@/lib/session";

/** Wireframe 5: what the crew opens on their phone — today's trips. */
export function CrewTodayPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user, crew } = useSession();
  const trips = useQuery({ queryKey: ["crew", "today"], queryFn: listTodayTrips });

  const start = useMutation({
    mutationFn: (routeRunId: string) => startTrip(routeRunId),
    onSuccess: async (trip) => {
      await queryClient.invalidateQueries({ queryKey: ["crew", "today"] });
      navigate(`/crew/trips/${trip.id}`);
    },
  });

  function open(trip: TripSummary) {
    if (trip.id) {
      navigate(`/crew/trips/${trip.id}`);
    } else {
      start.mutate(trip.route_run_id);
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-5 px-4 py-6">
      <div>
        <Eyebrow>Today</Eyebrow>
        <h1 className="font-display text-2xl font-bold tracking-tight">
          {user?.name ? `Morning, ${user.name.split(" ")[0]}` : "Your trips"}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {crew ? `You are on these runs as the ${crew.role}.` : "You are not on any run."}
        </p>
      </div>

      {trips.isPending ? <Loading label="Loading today's trips…" /> : null}
      <ErrorText error={trips.error} fallback="Could not load your trips." />
      <ErrorText error={start.error} fallback="Could not start that trip." />

      {trips.data && trips.data.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>No trips today</CardTitle>
            <CardDescription>
              The school has not put you on a run for today. Ask the school admin if that looks wrong.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : null}

      {trips.data?.map((trip) => (
        <Card key={trip.route_run_id}>
          <CardHeader>
            <Eyebrow>
              {trip.direction === "morning" ? "Morning run" : "Afternoon run"} ·{" "}
              {trip.departure_time.slice(0, 5)}
            </Eyebrow>
            <CardTitle>
              {trip.route_code} · {trip.route_name}
            </CardTitle>
            <CardDescription>
              {trip.vehicle_plate ? `${trip.vehicle_plate} · ` : ""}
              {trip.expected_count} {trip.expected_count === 1 ? "child" : "children"}
              {trip.status === "completed"
                ? ` · boarded ${trip.boarded_count}, dropped off ${trip.dropped_off_count}, absent ${trip.absent_count}`
                : ""}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => open(trip)} disabled={start.isPending} className="w-full sm:w-auto">
              {trip.status === "active"
                ? "Continue this trip"
                : trip.status === "completed"
                  ? "See what was recorded"
                  : start.isPending
                    ? "Starting…"
                    : "Start this trip"}
            </Button>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
