# Sprint 1 Spikes — Answers

> Tasks T1-11 to T1-14 from [`../../sprints/sprint-1.md`](../../sprints/sprint-1.md).
> Checked **8 October 2026**. Costs in USD and indicative KES (see note below).
> Labels: **FACT** (verified against a source today), **ASSUMPTION**, **UNKNOWN**.

Costs are quoted in USD; KES figures are indicative at roughly **KES 130 = USD 1** (ASSUMPTION — use the rate on
the day you sign anything). Vendors change pricing often: re-check before committing.

---

## T1-11 — Driver location with a locked screen

**Question:** can the driver's phone web app keep sending location while the screen is locked?

**Answer: no, not reliably.** Plan around keeping the screen on.

**FACT**

- The browser Geolocation API is tied to the document. When a mobile page is backgrounded or the screen locks,
  the browser suspends it, so `watchPosition` stops delivering. Neither Android Chrome nor iOS Safari grants a
  web page continuous background location. ([MDN Geolocation API](https://developer.mozilla.org/en-US/docs/Web/API/Geolocation_API))
- The Screen Wake Lock API is the only sanctioned way to stop the screen sleeping from a web page. Support
  (checked 8 Oct 2026): Chrome/Android 84+, Firefox 126+, Safari 16.4+.
  ([MDN Screen Wake Lock](https://developer.mozilla.org/en-US/docs/Web/API/Screen_Wake_Lock_API),
  [caniuse](https://caniuse.com/mdn-api_navigator_wakelock))
- Wake locks need a **secure context (HTTPS)**, and are **released automatically when the document becomes
  inactive** — the app must re-acquire on `visibilitychange`.
- iOS Safari is the weak spot: on iOS 16.4–18.3 the wake lock **does not work in a standalone Home Screen web
  app** (WebKit bug 254545, fixed in 18.4). Drivers on older iPhones who "install" the app will lose it.

**Options**

| Option | Works? | Cost / risk |
|---|---|---|
| Keep the screen on (wake lock) in a trip mode | Yes, with HTTPS and a recent browser | Battery and data use; iPhone homescreen quirk below iOS 18.4 |
| Foreground-only updates (driver keeps the app open) | Partly | Location gaps whenever the driver switches apps |
| Thin native wrapper (Capacitor) later | Yes — native background location | Extra build and store overhead; not MVP 1 |
| GPS/telematics device in the vehicle | Yes | Hardware and installation cost; not MVP 1 |
| Bluetooth/OBD dongle | UNKNOWN for this market | Procurement and support burden |

**Recommendation**

1. Driver trip mode uses a wake lock, with an explicit, unmissable "keep this screen open until the trip ends"
   state, and re-acquires the lock on `visibilitychange`.
2. Never let "bus approaching" be the only thing that works. Boarded, dropped off and absent are **taps**, and
   they keep working regardless of location.
3. If location stops mid-trip, mark that trip's "approaching" messages as unavailable rather than sending a
   wrong ETA, and log the gap.
4. Revisit a Capacitor wrapper only if pilot drivers routinely lock their phones — a Sprint 4+ decision, not now.

**What would change this answer:** user conversations (C-03) showing drivers must pocket the phone; a school
that already has telematics; evidence that iPhone 16.x is common among drivers.

---

## T1-12 — Maps and ETA

**Question:** what do we use to show the bus, and to decide "the bus is 5 minutes away"?

**Recommendation: split the problem.** Pay for nothing in the hot path.

| Need | Choice | Why |
|---|---|---|
| Show a bus on a map | **Leaflet + OpenStreetMap raster tiles** | No per-map-load billing; tiny bundle; good enough for one marker |
| Geocode school and stop addresses | **LocationIQ** free tier, Nominatim as a fallback | Generous free tier; OSM data; Kenya coverage is good in cities |
| Stop ordering for a route | **OpenRouteService / OSRM** | Free or self-hosted; only used when an admin edits a route |
| "5 minutes away" | **Compute it ourselves** from the driver's last GPS fix and the stop coordinates | Avoids a paid routing call per evaluation per child |

**FACT / ASSUMPTION**

- **ASSUMPTION.** Google Maps Platform still bills per SKU with a monthly free allowance, but the exact
  per-1,000-call prices and free tiers could not be read from the page today (it is JavaScript-rendered).
  Treat Google's numbers as UNKNOWN until someone opens the billing console.
  ([Google Maps Platform pricing](https://mapsplatform.google.com/pricing/))
- **ASSUMPTION.** Comparable alternatives — [Mapbox](https://www.mapbox.com/pricing),
  [HERE](https://www.here.com/get-started/pricing), [LocationIQ](https://locationiq.com/pricing),
  [OpenRouteService](https://openrouteservice.org/plans/) — each publish a free tier and then per-request
  pricing. Verify on the day.
- **FACT.** A per-call routing model is the wrong shape for Tafi: cost would scale with **children × stops ×
  trips**, every school day, for a product priced per child per month (D-07).

**How "5 minutes away" is actually computed**

Keep the driver's last few GPS fixes. When the driver is within a configurable threshold (default 1.5 km) of the
next stop, estimate arrival from the recent average speed, and require the estimate to hold for two consecutive
fixes before sending. Store the thresholds per school so a school can tune them (owner-decision row 9).

**What would change this answer:** a pilot school whose stops are in poorly mapped areas; the client insisting on
Google-grade ETA accuracy; or costs at scale proving self-hosting OSRM cheaper than a hosted tier.

---

## T1-13 — Worker: Celery vs RQ vs APScheduler

**Question:** what runs the WhatsApp sends and the scheduled jobs?

**Recommendation: keep Celery** (already wired in `backend/app/worker/celery_app.py`).

| Criterion | Celery | RQ | APScheduler + queue |
|---|---|---|---|
| Scheduled jobs | Celery Beat built in | Needs `rq-scheduler` | Native, but in-process |
| Retries / acks | First-class, configurable | Manual retry helpers | Manual |
| Observability | Flower, rich events | `rq-dashboard`, thinner | Weak |
| Ops burden | Highest config surface | Lowest | Low, but wrong shape |
| Multi-container safe | Yes | Yes | **No** — in-process scheduler duplicates jobs across workers |
| Redis fit | Yes | Yes (natural fit) | Yes |

**Reasoning.** Tafi needs both halves: asynchronous sends with retries and logging, and real scheduled work
(evaluating "bus approaching", daily cleanups, term reminders). APScheduler is disqualified as the primary
worker because running a scheduler inside more than one container duplicates jobs. RQ is the lighter option and
would be fine, but scheduling is a bolt-on. Celery already covers both and is the pattern the team has used in
production elsewhere (D-08).

**Swap cost is contained.** All Celery wiring lives in `backend/app/worker/celery_app.py`; tasks are declared
next to the code that owns them. If the team finds Celery's configuration slowing them down in Sprints 4–5,
moving to RQ touches that one module and the compose command.

**What would change this answer:** the team hitting a Celery configuration wall; or Sprint 4 showing the only
scheduled work is "evaluate approaching during an active trip", which could live in a lightweight loop.

---

## T1-14 — PostgreSQL: managed or container

**Question:** where does the database live in production?

**Recommendation: container for local development, DigitalOcean Managed PostgreSQL for staging and production.**

**FACT** (checked 8 Oct 2026, [DigitalOcean managed databases pricing](https://www.digitalocean.com/pricing/managed-databases))

- Managed PostgreSQL starts at **USD 15.15/month** (1 GiB RAM, 1 vCPU, 10 GiB storage), then 30.45, 60.90,
  122.10 and 244.35 for the larger single-node sizes.
- Additional storage is **USD 0.215/GiB/month**.
- Stripe-style line items and standby nodes cost extra.

| Criterion | Managed PostgreSQL | Container on the VPS |
|---|---|---|
| Cost at pilot scale | ~USD 15/month (≈ KES 2,000) | "Free" — but shares the VPS |
| Backups / PITR | Automated, restorable | Hand-rolled `pg_dump` + cron, untested until it matters |
| Patching | Vendor | The team |
| Connection limits | Managed and monitored | Defaults tuned by hand |
| Latency from the VPS | One private-network hop | Local |
| Path as schools are added | Resize in place | Migrate VPS → managed later anyway |

**Reasoning.** Tafi stores children's personal data, so backups are not a nice-to-have (Kenya DPA 2019 baseline,
owner-decision row 14). At roughly KES 2,000/month, managed buys automated backups and patching — the exact
things a two-person team forgets until an incident. The two `pg_dump`/`pg_restore` variants cost the same
either way if we move later, so starting managed removes the migration rather than deferring it.

**Practical detail.** The local compose stack keeps a containerised Postgres 16 with a named volume — that is a
development convenience only. Staging and production point at a managed cluster through `DATABASE_URL`; no code
changes.

**What would change this answer:** a genuinely zero budget for the pilot month, in which case run the container
with a nightly off-host `pg_dump` **and a weekly tested restore**.

---

## Effect on the plan

- Sprint 1 ships Celery and a containerised Postgres locally, as built.
- Sprint 2 (staging on DigitalOcean) provisions a managed Postgres cluster and passes `DATABASE_URL` as an
  environment variable. Budget item: roughly **USD 15/month** plus the droplet.
- Sprint 4 owns the driver trip mode: wake lock, the keep-screen-open state and the location-gap fallback.
- Anne's WhatsApp template work (T1-15) is unaffected, but "bus approaching" wording must survive a trip where
  location was lost.
