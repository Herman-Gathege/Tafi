import { Link } from "react-router-dom";

import { buttonStyles } from "@/components/ui/button-styles";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const steps = [
  {
    title: "The school sets up",
    body: "Routes, stops, vehicles, drivers and the children who ride — entered by hand or imported from a spreadsheet.",
  },
  {
    title: "The driver taps each child",
    body: "One tap on a phone marks a child boarded, dropped off or absent. Location is shared while the trip is running.",
  },
  {
    title: "Parents get the message",
    body: "WhatsApp updates go out as it happens. No app to download, no group to hunt through, no calling the school to ask.",
  },
];

const messages = [
  { time: "06:42", body: "Wanjiru boarded bus KCA 123X at 6:42." },
  { time: "06:58", body: "The bus is 5 minutes away from your stop." },
  { time: "16:10", body: "Wanjiru was dropped off at 16:10." },
];

export function LandingPage() {
  return (
    <div>
      <section className="border-b border-border bg-card">
        <div className="mx-auto w-full max-w-5xl px-4 py-14 sm:py-20">
          <p className="text-sm font-medium text-brand">Parent safety for school transport</p>
          <h1 className="mt-3 max-w-3xl font-display text-3xl leading-tight font-bold tracking-tight sm:text-5xl">
            Know the moment your child boards the school bus — and the moment they arrive.
          </h1>
          <p className="mt-5 max-w-2xl text-base text-muted-foreground sm:text-lg">
            Tafi sends parents a WhatsApp update for every school run. Boarded, on the way, dropped off. Schools
            run the transport from one place, and parents stop wondering.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link to="/wireframes" className={buttonStyles()}>
              See the wireframes
            </Link>
            <Link to="/signin" className={buttonStyles({ variant: "secondary" })}>
              School sign in
            </Link>
          </div>
          <p className="mt-4 text-xs text-muted-foreground">
            Tafi is being built now. The wireframes show the screens the pilot school will use.
          </p>
        </div>
      </section>

      <section className="mx-auto w-full max-w-5xl px-4 py-14">
        <h2 className="font-display text-2xl font-bold tracking-tight">How it works</h2>
        <ol className="mt-6 grid gap-4 sm:grid-cols-3">
          {steps.map((step, index) => (
            <li key={step.title}>
              <Card className="h-full">
                <CardHeader>
                  <p className="text-xs font-medium text-muted-foreground">Step {index + 1}</p>
                  <CardTitle>{step.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">{step.body}</p>
                </CardContent>
              </Card>
            </li>
          ))}
        </ol>
      </section>

      <section className="border-y border-border bg-card">
        <div className="mx-auto grid w-full max-w-5xl gap-8 px-4 py-14 lg:grid-cols-2 lg:items-center">
          <div>
            <h2 className="font-display text-2xl font-bold tracking-tight">What a parent sees</h2>
            <p className="mt-3 text-sm text-muted-foreground sm:text-base">
              Three messages carry the whole promise: the child is on the bus, the bus is close, the child is
              safely dropped off. If a message cannot be delivered, Tafi records why instead of staying silent.
            </p>
            <p className="mt-3 text-sm text-muted-foreground">
              Guardians use the WhatsApp they already have. Nothing to install, nothing to remember.
            </p>
          </div>
          <div className="rounded-2xl border border-border bg-background p-4">
            <ul className="flex flex-col gap-3">
              {messages.map((message) => (
                <li key={message.time} className="rounded-xl bg-safe-soft px-4 py-3">
                  <p className="text-xs font-medium text-safe">Tafi · {message.time}</p>
                  <p className="mt-1 text-sm">{message.body}</p>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-5xl px-4 py-14">
        <div className="grid gap-8 lg:grid-cols-2">
          <div>
            <h2 className="font-display text-2xl font-bold tracking-tight">Who it is for</h2>
            <ul className="mt-4 flex flex-col gap-3 text-sm text-muted-foreground">
              <li>
                <span className="font-medium text-foreground">Schools first.</span> They run the buses, keep the
                records and pay for Tafi.
              </li>
              <li>
                <span className="font-medium text-foreground">Parents and guardians.</span> They get the updates
                on WhatsApp and pay the school for transport, not Tafi.
              </li>
              <li>
                <span className="font-medium text-foreground">Independent transport providers later.</span> The
                same tools, outside a school.
              </li>
            </ul>
          </div>
          <div>
            <h2 className="font-display text-2xl font-bold tracking-tight">Children's information</h2>
            <p className="mt-4 text-sm text-muted-foreground">
              Tafi holds a child's name, class, route and a guardian's phone number — nothing more than the school
              needs to run transport. Guardians consent before the first message is sent, and we work to the Kenya
              Data Protection Act 2019.
            </p>
          </div>
        </div>
      </section>

      <section className="border-t border-border bg-card">
        <div className="mx-auto w-full max-w-5xl px-4 py-12 text-center">
          <h2 className="font-display text-2xl font-bold tracking-tight">Walk through the screens</h2>
          <p className="mx-auto mt-3 max-w-xl text-sm text-muted-foreground">
            Eleven screens covering the school portal, the crew app, the parent messages and the operator view.
          </p>
          <div className="mt-6 flex justify-center">
            <Link to="/wireframes" className={buttonStyles()}>
              Open the wireframes
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
