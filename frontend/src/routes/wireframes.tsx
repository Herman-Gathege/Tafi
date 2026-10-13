import { useCallback, useEffect, useRef, useState } from "react";

import { buttonStyles } from "@/components/ui/button-styles";
import { cn } from "@/lib/utils";

const DECK_SRC = "/wireframes/tafi-mvp1-wireframes.html";

/**
 * The deck is an export from a design tool, not a responsive page: it lays its
 * screens out on a fixed canvas (1440px wide for desktop screens, 390px for the
 * phone ones). We scale it to whatever width we have instead of letting it
 * scroll sideways, and stop shrinking once the text would be unreadable — below
 * that the deck pans, which is the honest way to read a desktop wireframe on a
 * phone.
 */
const MIN_ZOOM = 0.5;

interface Screen {
  /** Exact heading text in the exported deck, used to find the screen. */
  title: string;
  label: string;
  blurb: string;
}

interface Group {
  name: string;
  screens: Screen[];
}

const groups: Group[] = [
  {
    name: "School portal",
    screens: [
      {
        title: "School portal · Today",
        label: "Today",
        blurb: "The morning run: trips running, children boarded, and anything that needs attention.",
      },
      {
        title: "School portal · Children & guardians",
        label: "Children & guardians",
        blurb: "Riders with their route, stop and guardian, plus import and WhatsApp invite actions.",
      },
      {
        title: "School portal · Routes, vehicles & crew",
        label: "Routes, vehicles & crew",
        blurb: "The routes with their stops, and the vehicle and crew assigned to each.",
      },
      {
        title: "School portal · Trip detail",
        label: "Trip detail",
        blurb: "One trip: the stop order, who boarded where, and the timeline of what happened.",
      },
    ],
  },
  {
    name: "Crew app",
    screens: [
      {
        title: "Crew app · My trip today",
        label: "My trip today",
        blurb: "What the driver opens on their phone: today's trip, start and end controls.",
      },
      {
        title: "Crew app · Mark children on and off",
        label: "Mark children on and off",
        blurb: "Tapping each child boarded, dropped off or absent, one-handed.",
      },
      {
        title: "Crew app · Trip complete",
        label: "Trip complete",
        blurb: "The summary after a trip and what was recorded for every child.",
      },
    ],
  },
  {
    name: "Parent",
    screens: [
      {
        title: "Option A · Parent WhatsApp messages",
        label: "WhatsApp messages (Option A)",
        blurb: "Boarded, approaching, dropped off and absent — and what a failed message looks like.",
      },
      {
        title: "Option A · Registration page (from invite link)",
        label: "Registration from invite link (Option A)",
        blurb: "What a guardian sees when the school invites them, including the consent step.",
      },
      {
        title: "Option B · Parent web dashboard",
        label: "Parent web dashboard (Option B)",
        blurb: "A parent web view. Not in MVP 1 — it is one side of an open decision for the client.",
      },
    ],
  },
  {
    name: "Later phase",
    screens: [
      {
        title: "Transport operator · Overview (later phase)",
        label: "Transport operator overview",
        blurb: "A provider running several schools. After MVP 1.",
      },
    ],
  },
];

const allScreens = groups.flatMap((group) => group.screens);
const titles = new Set(allScreens.map((screen) => screen.title));

export function WireframesPage() {
  const frameRef = useRef<HTMLIFrameElement>(null);
  const deckRef = useRef<HTMLDivElement>(null);
  const naturalWidthRef = useRef<number | null>(null);
  const [offsets, setOffsets] = useState<Record<string, number>>({});
  const [active, setActive] = useState<string | null>(null);

  /**
   * Scale the deck to the frame, then record where each screen starts. The
   * export unpacks its screens with JavaScript, so this runs repeatedly until
   * every screen is accounted for.
   */
  const sync = useCallback(() => {
    const frame = frameRef.current;
    const doc = frame?.contentDocument;
    if (!frame || !doc) {
      return false;
    }

    // Measure the deck's natural width before any zoom is applied.
    if (naturalWidthRef.current === null) {
      const width = doc.documentElement.scrollWidth || doc.body.scrollWidth;
      if (width > 0) {
        naturalWidthRef.current = width;
      }
    }

    const available = frame.clientWidth;
    if (naturalWidthRef.current && available > 0) {
      const zoom = Math.max(MIN_ZOOM, Math.min(1, available / naturalWidthRef.current));
      const value = String(Math.round(zoom * 1000) / 1000);
      if (doc.documentElement.style.getPropertyValue("zoom") !== value) {
        doc.documentElement.style.setProperty("zoom", value);
      }
    }

    const de = doc.documentElement;
    const scrollTop = de.scrollTop || doc.body.scrollTop || 0;
    const found: Record<string, number> = {};

    for (const node of Array.from(doc.querySelectorAll<HTMLElement>("*"))) {
      if (node.children.length > 0) {
        continue;
      }
      const text = (node.textContent ?? "").trim();
      if (!titles.has(text)) {
        continue;
      }
      // The heading sits above its screen: aim at the screen itself.
      const host = node.parentElement;
      const sibling = host?.nextElementSibling;
      const target = sibling instanceof HTMLElement ? sibling : (host ?? node);
      const top = Math.max(0, target.getBoundingClientRect().top + scrollTop - 8);
      if (found[text] === undefined || top < found[text]) {
        found[text] = top;
      }
    }

    setOffsets(found);
    return Object.keys(found).length >= titles.size;
  }, []);

  useEffect(() => {
    const frame = frameRef.current;
    let attempts = 0;
    let timer: number | undefined;

    function tick() {
      attempts += 1;
      if (!sync() && attempts < 60) {
        timer = window.setTimeout(tick, 400);
      }
    }

    function onLoad() {
      // A reload means a fresh unpack: measure the width again.
      naturalWidthRef.current = null;
      attempts = 0;
      tick();
    }

    function onResize() {
      sync();
    }

    frame?.addEventListener("load", onLoad);
    window.addEventListener("resize", onResize);
    tick();

    return () => {
      if (timer) {
        window.clearTimeout(timer);
      }
      frame?.removeEventListener("load", onLoad);
      window.removeEventListener("resize", onResize);
    };
  }, [sync]);

  function openScreen(screen: Screen) {
    setActive(screen.title);
    // The deck may be below the list on a narrow screen, so bring it into view.
    deckRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });

    const top = offsets[screen.title];
    const frame = frameRef.current;
    if (frame?.contentWindow && top !== undefined) {
      frame.contentWindow.scrollTo({ top, behavior: "smooth" });
      return;
    }
    window.open(DECK_SRC, "_blank", "noopener");
  }

  const measured = Object.keys(offsets).length;

  function chipClass(isActive: boolean) {
    return cn(
      "rounded-full border px-3 py-1.5 text-xs font-medium whitespace-nowrap transition",
      isActive
        ? "border-primary bg-brand-soft text-foreground"
        : "border-border bg-card text-muted-foreground hover:text-foreground",
    );
  }

  return (
    <div className="mx-auto w-full max-w-[1600px] px-4 py-10">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">MVP 1 wireframes</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Eleven screens, drawn before any of them are built. Pick a screen to jump to it, or open the full deck
            in its own tab. These are a design preview, not the working product.
          </p>
        </div>
        <a href={DECK_SRC} target="_blank" rel="noreferrer" className={buttonStyles()}>
          Open the full deck
        </a>
      </div>

      {/* One jump bar above the deck, at every width, so a click is always visible. */}
      <nav aria-label="Jump to a wireframe screen" className="mt-8 flex flex-col gap-3">
        {groups.map((group) => (
          <div key={group.name}>
            <p className="text-[0.7rem] font-semibold tracking-wide text-muted-foreground uppercase">
              {group.name}
            </p>
            <ul className="mt-1.5 flex gap-2 overflow-x-auto pb-1">
              {group.screens.map((screen) => (
                <li key={screen.title}>
                  <button
                    type="button"
                    onClick={() => openScreen(screen)}
                    className={chipClass(active === screen.title)}
                    title={screen.blurb}
                  >
                    {screen.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
        <p className="text-xs text-muted-foreground">
          {measured}/{allScreens.length} screens ready in the preview.
        </p>
      </nav>

      <div
        ref={deckRef}
        className="mt-6 scroll-mt-20 overflow-hidden rounded-xl border border-border bg-card"
      >
        <iframe
          ref={frameRef}
          src={DECK_SRC}
          title="Tafi MVP 1 wireframes"
          className="h-[70vh] w-full lg:h-[calc(100dvh-10rem)]"
        />
      </div>
    </div>
  );
}
