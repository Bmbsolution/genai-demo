"use client";

import {
  ArrowRight,
  Bell,
  CalendarDays,
  Check,
  ClipboardCheck,
  MapPin,
  ShieldCheck,
  Share2,
  Sparkles,
  Users,
} from "lucide-react";
import Link from "next/link";

import { MarketingFooter } from "@/components/marketing/marketing-footer";
import { MarketingNav } from "@/components/marketing/marketing-nav";
import { Button } from "@/components/ui/button";

const FEATURES = [
  {
    icon: Share2,
    title: "One link, zero friction",
    body: "Send a single page. Guests RSVP in two taps — no app, no account to create.",
  },
  {
    icon: Users,
    title: "Know exactly who's coming",
    body: "Live counts, +1s, dietary needs, and an automatic waitlist when you reach capacity.",
  },
  {
    icon: Sparkles,
    title: "Pages that look designed",
    body: "Every event gets a clean, on-brand page you'll actually be proud to share.",
  },
  {
    icon: Bell,
    title: "Reminders that land",
    body: "Automatic nudges before the day so nobody forgets to show up.",
  },
  {
    icon: ClipboardCheck,
    title: "Effortless day-of check-in",
    body: "Tick guests off at the door from any phone — no clipboard required.",
  },
  {
    icon: ShieldCheck,
    title: "Private by design",
    body: "Each guest sees only their own invite. Their data stays yours, never sold.",
  },
];

const STEPS = [
  {
    n: "01",
    title: "Create your event",
    body: "Add the details — date, place, capacity. Two minutes, tops.",
  },
  {
    n: "02",
    title: "Invite your guests",
    body: "Share the link or send invites. Each guest gets a private RSVP page.",
  },
  {
    n: "03",
    title: "Watch the RSVPs roll in",
    body: "Track replies live, manage the list, and check guests in on the day.",
  },
];

const FAQ = [
  {
    q: "Do my guests need an account?",
    a: "No. Guests RSVP from a private link — no sign-up, no app to download.",
  },
  {
    q: "Can I collect dietary needs and +1s?",
    a: "Yes — add custom questions to your RSVP form and see the answers at a glance.",
  },
  {
    q: "Is my guests' data private?",
    a: "Always. Each guest sees only their own invite, and we never sell your data.",
  },
  {
    q: "Can I use Gatherly for free?",
    a: "Yes — the Free plan covers personal hosting. Upgrade to Pro anytime as you grow.",
  },
];

const HERO_GUESTS = [
  { name: "Marie D.", status: "Yes", cls: "border-success/30 bg-success/15 text-success" },
  { name: "Sam P.", status: "Maybe", cls: "border-warning/30 bg-warning/15 text-warning" },
  { name: "Priya N.", status: "Yes", cls: "border-success/30 bg-success/15 text-success" },
];

const FREE_FEATURES = [
  "Up to 3 active events",
  "50 guests per event",
  "Public event pages",
  "Live RSVP tracking",
];

const PRO_FEATURES = [
  "Unlimited events & guests",
  "Automatic reminders",
  "Custom branding",
  "CSV import & export",
  "Day-of check-in",
];

function HeroMock() {
  return (
    <div className="mx-auto w-full max-w-sm rounded-2xl border bg-card p-5 shadow-xl">
      <div className="mb-4 flex items-center justify-between">
        <span className="rounded-full border border-brand/20 bg-brand/10 px-2.5 py-0.5 text-xs font-semibold text-brand">
          Published
        </span>
        <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
          <Users className="h-3.5 w-3.5" /> 38 / 40
        </span>
      </div>
      <h3 className="font-display text-xl font-semibold tracking-tight">Summer Rooftop Party</h3>
      <div className="mt-2 space-y-1.5 text-sm text-muted-foreground">
        <p className="inline-flex items-center gap-2">
          <CalendarDays className="h-4 w-4" /> Sat, Aug 1 · 7:00 PM
        </p>
        <p className="inline-flex items-center gap-2">
          <MapPin className="h-4 w-4" /> The Skyline Loft
        </p>
      </div>
      <div className="mt-4 space-y-2 border-t border-border/60 pt-4">
        {HERO_GUESTS.map((guest) => (
          <div key={guest.name} className="flex items-center justify-between text-sm">
            <span className="font-medium">{guest.name}</span>
            <span
              className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${guest.cls}`}
            >
              {guest.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <MarketingNav />

      <section className="mx-auto grid max-w-6xl items-center gap-12 px-6 py-16 md:grid-cols-2 md:py-24">
        <div className="animate-fade-up">
          <span className="inline-flex items-center gap-2 rounded-full border border-border bg-muted/50 px-3 py-1 text-xs font-medium text-muted-foreground">
            <Sparkles className="h-3.5 w-3.5 text-brand" /> RSVPs your guests will love
          </span>
          <h1 className="mt-5 font-display text-4xl font-semibold leading-[1.08] tracking-tight sm:text-5xl">
            Host events people actually show up to.
          </h1>
          <p className="mt-5 max-w-md text-lg text-muted-foreground">
            Create an event, share one link, and track every RSVP in real time — with a guest
            experience as polished as your party.
          </p>
          <div className="mt-7 flex flex-wrap items-center gap-3">
            <Button asChild size="lg">
              <Link href="/signup">
                Get started — it&apos;s free <ArrowRight className="ml-1.5 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/login">Sign in</Link>
            </Button>
          </div>
          <p className="mt-3 text-xs text-muted-foreground">No credit card required.</p>
        </div>
        <div className="animate-fade-up [animation-delay:120ms]">
          <HeroMock />
        </div>
      </section>

      <section className="border-y border-border/70 bg-muted/30">
        <div className="mx-auto max-w-6xl px-6 py-5 text-center text-sm text-muted-foreground">
          Trusted by hosts planning meetups, weddings, team offsites, and everything in between.
        </div>
      </section>

      <section id="features" className="mx-auto max-w-6xl px-6 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-3xl font-semibold tracking-tight">
            Everything you need to fill the room
          </h2>
          <p className="mt-3 text-muted-foreground">
            From the first invite to the day-of door, Gatherly handles the details so you can host.
          </p>
        </div>
        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="rounded-xl border bg-card p-6 shadow-card transition-colors hover:border-brand/40"
            >
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand/10 text-brand">
                <feature.icon className="h-5 w-5" />
              </span>
              <h3 className="mt-4 font-display text-lg font-semibold tracking-tight">
                {feature.title}
              </h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{feature.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="how" className="border-t border-border/70 bg-muted/30">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="font-display text-3xl font-semibold tracking-tight">Live in three steps</h2>
            <p className="mt-3 text-muted-foreground">No setup call. No manual. Just your event.</p>
          </div>
          <div className="mt-12 grid gap-8 md:grid-cols-3">
            {STEPS.map((step) => (
              <div key={step.n}>
                <span className="font-mono text-sm font-semibold text-brand">{step.n}</span>
                <h3 className="mt-2 font-display text-xl font-semibold tracking-tight">
                  {step.title}
                </h3>
                <p className="mt-1.5 text-sm text-muted-foreground">{step.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="pricing" className="mx-auto max-w-6xl px-6 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-3xl font-semibold tracking-tight">
            Start free. Upgrade when you grow.
          </h2>
          <p className="mt-3 text-muted-foreground">Simple pricing, no surprises.</p>
        </div>
        <div className="mx-auto mt-12 grid max-w-3xl gap-6 sm:grid-cols-2">
          <div className="rounded-2xl border bg-card p-7 shadow-card">
            <p className="font-display text-lg font-semibold">Free</p>
            <p className="mt-2">
              <span className="font-display text-4xl font-semibold tracking-tight">$0</span>
              <span className="text-muted-foreground"> / forever</span>
            </p>
            <p className="mt-1 text-sm text-muted-foreground">For personal hosts.</p>
            <ul className="mt-6 space-y-2.5 text-sm">
              {FREE_FEATURES.map((item) => (
                <li key={item} className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 shrink-0 text-success" /> {item}
                </li>
              ))}
            </ul>
            <Button asChild variant="outline" className="mt-7 w-full">
              <Link href="/signup">Start free</Link>
            </Button>
          </div>
          <div className="relative rounded-2xl border-2 border-brand bg-card p-7 shadow-card">
            <span className="absolute -top-3 left-7 rounded-full bg-primary px-3 py-1 text-xs font-semibold text-primary-foreground">
              Most popular
            </span>
            <p className="font-display text-lg font-semibold">Pro</p>
            <p className="mt-2">
              <span className="font-display text-4xl font-semibold tracking-tight">$12</span>
              <span className="text-muted-foreground"> / month</span>
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              For frequent &amp; professional hosts.
            </p>
            <ul className="mt-6 space-y-2.5 text-sm">
              {PRO_FEATURES.map((item) => (
                <li key={item} className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 shrink-0 text-success" /> {item}
                </li>
              ))}
            </ul>
            <Button asChild className="mt-7 w-full">
              <Link href="/signup">Start Pro</Link>
            </Button>
          </div>
        </div>
      </section>

      <section id="faq" className="border-t border-border/70 bg-muted/30">
        <div className="mx-auto max-w-3xl px-6 py-20">
          <h2 className="text-center font-display text-3xl font-semibold tracking-tight">
            Questions, answered
          </h2>
          <div className="mt-10 divide-y divide-border/70 rounded-xl border bg-card">
            {FAQ.map((item) => (
              <details key={item.q} className="group p-5 [&_summary]:cursor-pointer">
                <summary className="flex list-none items-center justify-between font-medium">
                  {item.q}
                  <span className="ml-4 text-muted-foreground transition-transform group-open:rotate-45">
                    +
                  </span>
                </summary>
                <p className="mt-3 text-sm text-muted-foreground">{item.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-20">
        <div className="rounded-2xl border bg-card px-8 py-14 text-center shadow-card">
          <h2 className="font-display text-3xl font-semibold tracking-tight">
            Your next event deserves a better RSVP.
          </h2>
          <p className="mx-auto mt-3 max-w-md text-muted-foreground">
            Join the hosts making it effortless to gather the people they love.
          </p>
          <Button asChild size="lg" className="mt-7">
            <Link href="/signup">
              Get started — it&apos;s free <ArrowRight className="ml-1.5 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </section>

      <MarketingFooter />
    </div>
  );
}
