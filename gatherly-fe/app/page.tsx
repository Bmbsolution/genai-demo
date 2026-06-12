"use client";

import {
  ArrowRight,
  Bell,
  CalendarCheck,
  Check,
  ClipboardCheck,
  Quote,
  Share2,
  ShieldCheck,
  Sparkles,
  Star,
} from "lucide-react";
import Link from "next/link";

import { HeroDashboard } from "@/components/marketing/hero-dashboard";
import { CreateArt, ShareArt, TrackArt } from "@/components/marketing/illustrations";
import { MarketingFooter } from "@/components/marketing/marketing-footer";
import { MarketingNav } from "@/components/marketing/marketing-nav";
import { Counter, Parallax, ScrollProgress } from "@/components/marketing/motion";
import { Reveal } from "@/components/marketing/reveal";
import { Button } from "@/components/ui/button";

const STATS = [
  { to: 12, suffix: "K+", decimals: 0, label: "Events hosted" },
  { to: 480, suffix: "K", decimals: 0, label: "RSVPs collected" },
  { to: 78, suffix: "%", decimals: 0, label: "Avg response rate" },
  { to: 4.9, suffix: "/5", decimals: 1, label: "Host rating" },
];

const FEATURES = [
  {
    icon: Share2,
    title: "See every reply, live",
    body: "Yes, no, maybe, +1s and dietary needs — updating the moment a guest taps, with an automatic waitlist at capacity.",
  },
  {
    icon: Bell,
    title: "Reminders that land",
    body: "Automated nudges go out before the day, so attendance never slips through the cracks.",
  },
  {
    icon: ClipboardCheck,
    title: "Door-ready check-in",
    body: "Tick guests off from any phone as they arrive — a clean, professional front desk with no clipboard.",
  },
  {
    icon: CalendarCheck,
    title: "Readiness, at a glance",
    body: "Response rates, capacity, and what each event still needs before the day — on one dashboard.",
  },
  {
    icon: Sparkles,
    title: "Pages that look designed",
    body: "Every event gets a clean, on-brand page your guests will actually be proud to open.",
  },
  {
    icon: ShieldCheck,
    title: "Private by design",
    body: "Each guest sees only their own invite. Their data stays yours — never sold, never shared.",
  },
];

const STEPS = [
  {
    n: "01",
    Art: CreateArt,
    title: "Create your event",
    body: "Add the details — date, place, capacity. Two minutes, tops.",
  },
  {
    n: "02",
    Art: ShareArt,
    title: "Invite your guests",
    body: "Share the link or send invites. Each guest gets a private RSVP page.",
  },
  {
    n: "03",
    Art: TrackArt,
    title: "Watch the RSVPs roll in",
    body: "Track replies live, manage the list, and check guests in on the day.",
  },
];

const PHOTO_POINTS = [
  "Real-time RSVPs, no spreadsheets",
  "Automatic waitlists at capacity",
  "Check-in that works at the door",
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

const FREE_FEATURES = [
  "Up to 3 active events",
  "50 guests per event",
  "Public event pages",
  "Live RSVP tracking",
];

const PRO_FEATURES = [
  "Unlimited events & guests",
  "Automated reminders",
  "CSV import & export",
  "Day-of check-in",
  "Insights & readiness",
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background font-sans">
      <ScrollProgress />
      <MarketingNav />

      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="relative overflow-hidden border-b border-border/60 bg-muted/20">
        <div className="mx-auto grid max-w-6xl items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-24">
          <div className="animate-fade-up">
            <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs font-semibold text-muted-foreground shadow-soft">
              <span className="h-1.5 w-1.5 rounded-full bg-brand" /> Gatherly 2.0 is live
            </span>
            <h1 className="mt-5 font-display text-4xl font-bold leading-[1.1] tracking-tight text-foreground sm:text-5xl lg:text-[3.4rem]">
              Host events people actually show up to.
            </h1>
            <p className="mt-5 max-w-md text-lg leading-relaxed text-muted-foreground">
              The modern event-management platform for professionals. Real-time RSVPs, automated
              reminders, and a frictionless experience from invitation to check-in.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Button asChild size="lg" className="rounded-lg">
                <Link href="/signup">
                  Start for free <ArrowRight className="ml-1.5 h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="rounded-lg">
                <Link href="/login">Sign in</Link>
              </Button>
            </div>
            <div className="mt-8 flex items-center gap-4">
              <div className="flex -space-x-2.5">
                {["MD", "SP", "PN", "JL"].map((i) => (
                  <span
                    key={i}
                    className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-background bg-muted text-[10px] font-semibold text-muted-foreground"
                  >
                    {i}
                  </span>
                ))}
              </div>
              <div className="text-xs text-muted-foreground">
                <span className="inline-flex text-gold">
                  {[0, 1, 2, 3, 4].map((s) => (
                    <Star key={s} className="h-3.5 w-3.5 fill-current" />
                  ))}
                </span>
                <p className="mt-0.5">Trusted by 1,200+ hosts</p>
              </div>
            </div>
          </div>

          <div className="animate-fade-up [animation-delay:120ms]">
            <Parallax speed={0.05} className="flex justify-center lg:justify-end">
              <div className="animate-float-slow">
                <HeroDashboard />
              </div>
            </Parallax>
          </div>
        </div>
      </section>

      {/* ── Stats banner ─────────────────────────────────────── */}
      <section className="border-b border-border/60 bg-card">
        <div className="mx-auto grid max-w-6xl grid-cols-2 divide-y divide-border/60 px-6 py-10 sm:grid-cols-4 sm:divide-x sm:divide-y-0">
          {STATS.map((s, i) => (
            <Reveal key={s.label} delay={i * 80} className="px-2 py-3 text-center sm:py-0">
              <Counter
                to={s.to}
                decimals={s.decimals}
                suffix={s.suffix}
                className="font-display text-3xl font-bold tracking-tight text-foreground tabular-nums"
              />
              <p className="mt-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {s.label}
              </p>
            </Reveal>
          ))}
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────────── */}
      <section id="features" className="mx-auto max-w-6xl px-6 py-20 lg:py-28">
        <Reveal className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            Everything you need to fill the room
          </h2>
          <p className="mt-4 text-muted-foreground">
            We stripped away the clutter so you can focus on your guests — powerful tools wrapped in
            a beautifully simple interface.
          </p>
        </Reveal>
        <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature, i) => (
            <Reveal
              key={feature.title}
              delay={(i % 3) * 80}
              as="article"
              className="group rounded-xl border border-border/70 bg-card p-7 shadow-soft transition-all duration-300 hover:-translate-y-1 hover:shadow-lift"
            >
              <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-brand/10 text-brand transition-colors group-hover:bg-brand group-hover:text-white">
                <feature.icon className="h-5 w-5" />
              </span>
              <h3 className="mt-5 font-display text-lg font-bold tracking-tight text-foreground">
                {feature.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{feature.body}</p>
            </Reveal>
          ))}
        </div>
      </section>

      {/* ── How it works ─────────────────────────────────────── */}
      <section id="how" className="border-y border-border/60 bg-muted/20">
        <div className="mx-auto max-w-6xl px-6 py-20 lg:py-28">
          <Reveal className="mx-auto max-w-2xl text-center">
            <h2 className="font-display text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Live in three steps
            </h2>
            <p className="mt-4 text-muted-foreground">No setup call. No manual. Just your event.</p>
          </Reveal>
          <div className="mt-14 grid gap-6 md:grid-cols-3">
            {STEPS.map((step, i) => (
              <Reveal
                key={step.n}
                delay={i * 120}
                as="article"
                className="draw rounded-xl border border-border/70 bg-card p-7 shadow-soft"
              >
                <div className="rounded-lg bg-muted/40 p-3">
                  <step.Art />
                </div>
                <span className="mt-6 inline-block font-mono text-sm font-bold text-brand">
                  {step.n}
                </span>
                <h3 className="mt-1 font-display text-xl font-bold tracking-tight text-foreground">
                  {step.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{step.body}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ── Photo band ───────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-6 py-20 lg:py-28">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          <Reveal variant="left" className="overflow-hidden rounded-2xl border border-border/60 shadow-lift">
            <Parallax speed={0.08}>
              {/* eslint-disable-next-line @next/next/no-img-element -- local marketing photo */}
              <img
                src="/hero-event.webp"
                alt="A team coordinating an event together"
                loading="lazy"
                className="aspect-[16/11] w-full scale-110 object-cover"
              />
            </Parallax>
          </Reveal>
          <Reveal variant="right">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand">
              Built for modern teams
            </span>
            <h2 className="mt-2 font-display text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Run every gathering like a professional
            </h2>
            <p className="mt-4 max-w-md text-muted-foreground">
              From a backyard birthday to a 300-seat conference, Gatherly keeps the whole team in
              sync — one source of truth from the first invite to the last check-in.
            </p>
            <ul className="mt-6 space-y-3">
              {PHOTO_POINTS.map((point) => (
                <li key={point} className="flex items-center gap-3 text-sm font-medium">
                  <span className="flex h-5 w-5 items-center justify-center rounded-md bg-brand/10 text-brand">
                    <Check className="h-3.5 w-3.5" />
                  </span>
                  {point}
                </li>
              ))}
            </ul>
            <Button asChild className="mt-8 rounded-lg">
              <Link href="/signup">
                Get started <ArrowRight className="ml-1.5 h-4 w-4" />
              </Link>
            </Button>
          </Reveal>
        </div>
      </section>

      {/* ── Testimonial (dark) ───────────────────────────────── */}
      <section className="bg-navy">
        <div className="mx-auto max-w-3xl px-6 py-20 text-center lg:py-28">
          <Reveal>
            <Quote className="mx-auto h-9 w-9 text-brand" />
            <p className="mt-6 font-display text-2xl font-semibold leading-snug tracking-tight text-white sm:text-3xl">
              “Gatherly turned our messy spreadsheets into a sleek, professional experience. Our
              250-person launch went off without a single hiccup at the door.”
            </p>
            <div className="mt-8 flex items-center justify-center gap-3">
              {/* eslint-disable-next-line @next/next/no-img-element -- decorative portrait */}
              <img
                src="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=96&q=80&auto=format&fit=crop"
                alt="Elena Rossi"
                loading="lazy"
                referrerPolicy="no-referrer"
                className="h-11 w-11 rounded-full border border-navy-line object-cover"
              />
              <div className="text-left">
                <p className="text-sm font-semibold text-white">Elena Rossi</p>
                <p className="text-xs text-white/60">Head of Events, Northwind</p>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ── Pricing ──────────────────────────────────────────── */}
      <section id="pricing" className="mx-auto max-w-6xl px-6 py-20 lg:py-28">
        <Reveal className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            Start free. Upgrade when you grow.
          </h2>
          <p className="mt-4 text-muted-foreground">Simple, transparent pricing — no surprises.</p>
        </Reveal>
        <div className="mx-auto mt-14 grid max-w-3xl items-start gap-6 sm:grid-cols-2">
          <Reveal variant="left" className="rounded-xl border border-border/70 bg-card p-8 shadow-soft">
            <p className="font-display text-lg font-bold text-foreground">Personal</p>
            <p className="mt-3">
              <span className="font-display text-4xl font-bold tracking-tight text-foreground">
                $0
              </span>
              <span className="text-muted-foreground"> / forever</span>
            </p>
            <p className="mt-1 text-sm text-muted-foreground">For personal hosts.</p>
            <ul className="mt-7 space-y-3 text-sm">
              {FREE_FEATURES.map((item) => (
                <li key={item} className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 shrink-0 text-brand" /> {item}
                </li>
              ))}
            </ul>
            <Button asChild variant="outline" className="mt-8 w-full rounded-lg">
              <Link href="/signup">Start free</Link>
            </Button>
          </Reveal>
          <Reveal
            variant="right"
            delay={100}
            className="relative rounded-xl border border-navy bg-navy p-8 shadow-lift"
          >
            <span className="absolute -top-3 left-8 inline-flex items-center gap-1 rounded-md bg-brand px-3 py-1 text-xs font-semibold text-white">
              <Sparkles className="h-3 w-3" /> Best value
            </span>
            <p className="font-display text-lg font-bold text-white">Pro</p>
            <p className="mt-3">
              <span className="font-display text-4xl font-bold tracking-tight text-white">
                $12
              </span>
              <span className="text-white/60"> / month</span>
            </p>
            <p className="mt-1 text-sm text-white/60">For frequent &amp; professional hosts.</p>
            <ul className="mt-7 space-y-3 text-sm text-white/90">
              {PRO_FEATURES.map((item) => (
                <li key={item} className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 shrink-0 text-brand" /> {item}
                </li>
              ))}
            </ul>
            <Button asChild className="mt-8 w-full rounded-lg">
              <Link href="/signup">Start Pro</Link>
            </Button>
          </Reveal>
        </div>
      </section>

      {/* ── FAQ ──────────────────────────────────────────────── */}
      <section id="faq" className="border-y border-border/60 bg-muted/20">
        <div className="mx-auto max-w-3xl px-6 py-20 lg:py-28">
          <Reveal>
            <h2 className="text-center font-display text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Questions, answered
            </h2>
          </Reveal>
          <Reveal
            delay={80}
            className="mt-10 divide-y divide-border/70 overflow-hidden rounded-xl border border-border/70 bg-card shadow-soft"
          >
            {FAQ.map((item) => (
              <details key={item.q} className="group p-6 [&_summary]:cursor-pointer">
                <summary className="flex list-none items-center justify-between font-semibold text-foreground">
                  {item.q}
                  <span className="ml-4 text-muted-foreground transition-transform group-open:rotate-45">
                    +
                  </span>
                </summary>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{item.a}</p>
              </details>
            ))}
          </Reveal>
        </div>
      </section>

      {/* ── Final CTA ────────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-6 py-20 lg:py-24">
        <Reveal className="overflow-hidden rounded-2xl bg-navy px-8 py-16 text-center">
          <h2 className="font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Your next event deserves a better RSVP.
          </h2>
          <p className="mx-auto mt-4 max-w-md text-white/70">
            Join the professionals making it effortless to gather the people who matter.
          </p>
          <Button asChild size="lg" className="mt-8 rounded-lg">
            <Link href="/signup">
              Start for free <ArrowRight className="ml-1.5 h-4 w-4" />
            </Link>
          </Button>
          <p className="mt-3 text-xs text-white/50">No credit card required.</p>
        </Reveal>
      </section>

      <MarketingFooter />
    </div>
  );
}
