import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorText, Eyebrow, Loading } from "@/components/ui/feedback";
import {
  confirmStopped,
  endTrip,
  getTrip,
  markChild,
  shareLocation,
  type BoardingKind,
  type ChildOnTrip,
} from "@/lib/api";
import { cn } from "@/lib/utils";

/**
 * Wireframes 6 and 7: marking children on a trip, and the summary when it ends.
 *
 * A driver working alone must confirm the vehicle is stopped before marking (D-21). The
 * server checks how recent that confirmation is; this screen just collects it.
 */
export function CrewTripPage() {
  const { tripId } = useParams<{ tripId: string }>();
  const queryClient = useQueryClient();
  const [stoppedAt, setStoppedAt] = useState<string | null>(null);
  const [sharing, setSharing] = useState(false);
  const [locationNote, setLocationNote] = useState<string | null>(null);
  const lastSent = useRef(0);

  const trip = useQuery({
    queryKey: ["crew", "trip", tripId],
    queryFn: () => getTrip(tripId as string),
    enabled: Boolean(tripId),
    refetchInterval: 20_000,
  });

  const refresh = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: ["crew", "trip", tripId] });
  }, [queryClient, tripId]);

  const confirm = useMutation({
    mutationFn: () => confirmStopped(tripId as string),
    onSuccess: (result) => setStoppedAt(result.confirmed_at),
  });

  const mark = useMutation({
    mutationFn: (payload: { student_id: string; kind: BoardingKind }) =>
      markChild(tripId as string, { ...payload, stopped_confirmed_at: stoppedAt }),
    onSettled: refresh,
  });

  const finish = useMutation({
    mutationFn: () => endTrip(tripId as string),
    onSettled: refresh,
  });

  const needsConfirmation =
    trip.data?.status === "active" && trip.data.driver_alone && trip.data.my_role === "driver";
  const confirmationIsFresh = useRecent(stoppedAt, 110);
  const canMark = trip.data?.status === "active" && (!needsConfirmation || confirmationIsFresh);

  // Location: a phone browser cannot keep sending this with the screen locked (T1-11),
  // so the crew member keeps this screen open and the app says so plainly.
  useEffect(() => {
    if (!sharing || !tripId || typeof navigator === "undefined" || !navigator.geolocation) {
      return;
    }
    setLocationNote("Sharing while this screen stays open.");
    const watch = navigator.geolocation.watchPosition(
      (position) => {
        const now = Date.now();
        if (now - lastSent.current < 10_000) {
          return;
        }
        lastSent.current = now;
        void shareLocation(tripId, {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy_m: position.coords.accuracy ?? null,
        })
          .then(() => setLocationNote("Location sent."))
          .catch(() => setLocationNote("Could not send your location — the trip keeps recording."));
      },
      (error) => {
        setSharing(false);
        setLocationNote(
          error.code === error.PERMISSION_DENIED
            ? "Location is blocked. The trip still records who boarded; no bus-approaching message will go out."
            : "Location is unavailable. The trip still records who boarded.",
        );
      },
      { enableHighAccuracy: true, maximumAge: 5_000, timeout: 20_000 },
    );
    return () => navigator.geolocation.clearWatch(watch);
  }, [sharing, tripId]);

  if (trip.isPending) {
    return <div className="p-6"><Loading label="Loading the trip…" /></div>;
  }
  if (trip.isError || !trip.data) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-10">
        <ErrorText error={trip.error} fallback="Could not load this trip." />
        <Link to="/crew" className="text-sm underline">Back to today's trips</Link>
      </div>
    );
  }

  const data = trip.data;
  const done = data.status === "completed";

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-5 px-4 py-6">
      <div>
        <Eyebrow>
          {data.direction === "morning" ? "Morning run" : "Afternoon run"} ·{" "}
          {data.departure_time.slice(0, 5)}
          {data.vehicle_plate ? ` · ${data.vehicle_plate}` : ""}
        </Eyebrow>
        <h1 className="font-display text-2xl font-bold tracking-tight">
          {data.route_code} · {data.route_name}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {done
            ? `Trip finished. ${data.boarded_count} boarded, ${data.dropped_off_count} dropped off, ${data.absent_count} absent.`
            : `${data.boarded_count} of ${data.children.length} on board · ${plural(data.location_count, "location update")}`}
        </p>
      </div>

      {needsConfirmation && !done ? (
        <Card className={cn(confirmationIsFresh ? "border-safe" : "border-destructive")}>
          <CardHeader>
            <CardTitle>{confirmationIsFresh ? "Marks are unlocked" : "Are you stopped?"}</CardTitle>
            <CardDescription>
              {confirmationIsFresh
                ? "You confirmed a moment ago. Confirm again once you move on."
                : "You are driving alone, so children can only be marked while the vehicle is stopped."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => confirm.mutate()} disabled={confirm.isPending} className="w-full">
              {confirm.isPending ? "Confirming…" : "I am stopped"}
            </Button>
          </CardContent>
        </Card>
      ) : null}

      <ErrorText error={mark.error} fallback="Could not save that mark." />
      <ErrorText error={confirm.error} fallback="Could not confirm." />
      <ErrorText error={finish.error} fallback="Could not end the trip." />

      <Card>
        <CardHeader>
          <CardTitle>Children</CardTitle>
          <CardDescription>
            {done ? "What was recorded on this trip." : "Tap each child as they get on or off."}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col divide-y divide-border">
          {data.children.length === 0 ? (
            <p className="text-sm text-muted-foreground">No children are on this route today.</p>
          ) : null}
          {data.children.map((child) => (
            <ChildRow
              key={child.student_id}
              child={child}
              disabled={!canMark || mark.isPending}
              onMark={(kind) => mark.mutate({ student_id: child.student_id, kind })}
            />
          ))}
        </CardContent>
      </Card>

      {!done ? (
        <Card>
          <CardHeader>
            <CardTitle>Share my location</CardTitle>
            <CardDescription>
              Keep this screen open while sharing — a phone browser stops sending location when the screen
              locks, and the battery can end it too.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <Button variant={sharing ? "secondary" : "primary"} onClick={() => setSharing((on) => !on)}>
              {sharing ? "Stop sharing" : "Start sharing"}
            </Button>
            {locationNote ? <p className="text-xs text-muted-foreground">{locationNote}</p> : null}
            <p className="text-xs text-muted-foreground">
              {plural(data.location_count, "update")} sent
              {data.last_location_at ? ` · last at ${new Date(data.last_location_at).toLocaleTimeString()}` : ""}
            </p>
          </CardContent>
        </Card>
      ) : null}

      {!done ? (
        <Button onClick={() => finish.mutate()} disabled={finish.isPending} className="w-full">
          {finish.isPending ? "Ending…" : "End this trip"}
        </Button>
      ) : (
        <Link to="/crew" className="text-center text-sm underline">
          Back to today's trips
        </Link>
      )}
    </div>
  );
}

function ChildRow({
  child,
  disabled,
  onMark,
}: {
  child: ChildOnTrip;
  disabled: boolean;
  onMark: (kind: BoardingKind) => void;
}) {
  const state = child.state;
  return (
    <div className="flex flex-col gap-2 py-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="text-sm font-medium">
          {child.first_name} {child.last_name}
        </p>
        <p className="text-xs text-muted-foreground">
          {child.grade ? `${child.grade} · ` : ""}
          {child.pickup_stop ?? "no stop"}
          {state === "pending" ? "" : ` · ${state.replace("_", " ")}`}
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button
          size="sm"
          variant={state === "boarded" ? "primary" : "secondary"}
          disabled={disabled || state === "boarded" || state === "dropped_off"}
          onClick={() => onMark("boarded")}
        >
          On
        </Button>
        <Button
          size="sm"
          variant={state === "dropped_off" ? "primary" : "secondary"}
          disabled={disabled || state !== "boarded"}
          onClick={() => onMark("dropped_off")}
        >
          Off
        </Button>
        <Button
          size="sm"
          variant="ghost"
          disabled={disabled || state !== "pending"}
          onClick={() => onMark("absent")}
        >
          Absent
        </Button>
      </div>
    </div>
  );
}

/** True while a timestamp is younger than `seconds` — the UI's copy of the server's window. */
function plural(count: number, word: string): string {
  return `${count} ${word}${count === 1 ? "" : "s"}`;
}

function useRecent(timestamp: string | null, seconds: number): boolean {
  const [fresh, setFresh] = useState(false);
  useEffect(() => {
    if (!timestamp) {
      setFresh(false);
      return;
    }
    const check = () => setFresh(Date.now() - new Date(timestamp).getTime() < seconds * 1000);
    check();
    const timer = window.setInterval(check, 5_000);
    return () => window.clearInterval(timer);
  }, [timestamp, seconds]);
  return fresh;
}
