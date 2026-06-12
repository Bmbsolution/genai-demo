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
  Users,
} from "lucide-react";
import Link from "next/link";

import { CreateArt, HeroDecor, ShareArt, TrackArt } from "@/components/marketing/illustrations";
import { MarketingFooter } from "@/components/marketing/marketing-footer";
import { MarketingNav } from "@/components/marketing/marketing-nav";
import {
  Confetti,
  EventCardMock,
  GuestBoardMock,
  InsightsMock,
  RsvpPhoneMock,
} from "@/components/marketing/mockups";
import { Counter, Parallax, Tilt } from "@/components/marketing/motion";
import { Reveal } from "@/components/marketing/reveal";
import { Button } from "@/components/ui/button";

const STATS = [
  { to: 12, suffix: "k+", decimals: 0, label: "events hosted" },
  { to: 480, suffix: "k", decimals: 0, label: "RSVPs collected" },
  { to: 78, suffix: "%", decimals: 0, label: "avg. response rate" },
  { to: 4.9, suffix: "★", decimals: 1, label: "host rating" },
];

const OCCASIONS = [
  "Birthdays",
  "Weddings",
  "Team offsites",
  "Meetups",
  "Conferences",
  "Dinner parties",
  "Launch parties",
  "Fundraisers",
  "Reunions",
  "Workshops",
];

const FEATURES = [
  {
    icon: Share2,
    title: "One link, zero friction",
    body: "Send a single page. Guests RSVP in two taps — no app, no account to create.",
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
    icon: CalendarCheck,
    title: "Readiness, at a glance",
    body: "See response rates, capacity, and what each event still needs before the day.",
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

const GALLERY = [
  { src: "1530103862676-de8c9debad1d", label: "Birthdays" },
  { src: "1511795409834-ef04bbd61622", label: "Parties" },
  { src: "1505373877841-8d25f7d46678", label: "Meetups" },
  { src: "1519225421980-715cb0215aed", label: "Weddings" },
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
  "Automatic reminders",
  "CSV import & export",
  "Day-of check-in",
  "Insights & readiness",
];

function unsplash(id: string, w = 600) {
  return `https://images.unsplash.com/photo-${id}?w=${w}&q=80&auto=format&fit=crop`;
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <MarketingNav />

      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        <div className="bg-dots pointer-events-none absolute inset-0 [mask-image:radial-gradient(ellipse_70%_60%_at_50%_0%,black,transparent)]" />
        <span className="halo bg-brand/25" style={{ width: 420, height: 420, top: -120, left: -80 }} />
        <span className="halo bg-gold/15" style={{ width: 320, height: 320, bottom: -60, right: -40 }} />

        <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-24">
          <div className="animate-fade-up">
            <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card/70 px-3 py-1 text-xs font-medium text-muted-foreground shadow-soft backdrop-blur">
              <Sparkles className="h-3.5 w-3.5 text-brand" /> RSVPs your guests will love
            </span>
            <h1 className="mt-5 text-balance font-display text-4xl font-semibold leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl">
              Host events people <span className="text-brand">actually show up</span> to.
            </h1>
            <p className="mt-5 max-w-md text-lg text-muted-foreground">
              Create an event, share one link, and track every RSVP in real time — with a guest
              experience as polished as your party.
            </p>
            <div className="mt-7 flex flex-wrap items-center gap-3">
              <Button asChild size="lg" className="shadow-glow">
                <Link href="/signup">
                  Get started — it&apos;s free <ArrowRight className="ml-1.5 h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <Link href="/login">Sign in</Link>
              </Button>
            </div>
            <div className="mt-7 flex items-center gap-4">
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
                <p className="mt-0.5">Loved by 1,200+ hosts</p>
              </div>
            </div>
          </div>

          {/* Layered, floating product composition with depth */}
          <div className="relative mx-auto h-[420px] w-full max-w-md animate-fade-up [animation-delay:120ms] lg:h-[460px]">
            <HeroDecor className="absolute inset-0 h-full w-full scale-[1.35]" />
            <div className="absolute left-1/2 top-1/2 w-full -translate-x-1/2 -translate-y-1/2">
              <div className="animate-float-slow">
                <Tilt>
                  <EventCardMock className="mx-auto shadow-lift" />
                </Tilt>
              </div>
            </div>
            <Parallax speed={0.32} className="absolute -right-2 -top-2 hidden sm:block">
              <div className="animate-float">
                <InsightsMock />
              </div>
            </Parallax>
            <Parallax speed={0.18} className="absolute -bottom-4 -left-2 hidden sm:block">
              <div className="animate-float-slow [animation-delay:1s]">
                <RsvpPhoneMock />
              </div>
            </Parallax>
          </div>
        </div>

        {/* Stats strip with counting numbers */}
        <div className="relative border-y border-border/70 bg-card/40 backdrop-blur">
          <div className="mx-auto grid max-w-6xl grid-cols-2 gap-px px-6 py-6 sm:grid-cols-4">
            {STATS.map((s, i) => (
              <Reveal key={s.label} delay={i * 80} className="text-center">
                <Counter
                  to={s.to}
                  decimals={s.decimals}
                  suffix={s.suffix}
                  className="font-display text-2xl font-semibold tracking-tight tabular-nums sm:text-3xl"
                />
                <p className="mt-0.5 text-xs text-muted-foreground sm:text-sm">{s.label}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ── Occasions marquee ────────────────────────────────── */}
      <div className="marquee relative overflow-hidden border-b border-border/70 py-4 [mask-image:linear-gradient(to_right,transparent,black_8%,black_92%,transparent)]">
        <div className="flex w-max animate-marquee gap-3">
          {[...OCCASIONS, ...OCCASIONS].map((occ, i) => (
            <span
              key={`${occ}-${i}`}
              className="inline-flex items-center gap-2 whitespace-nowrap rounded-full border bg-card px-4 py-1.5 text-sm font-medium text-muted-foreground"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-brand" />
              {occ}
            </span>
          ))}
        </div>
      </div>

      {/* ── Feature bento ────────────────────────────────────── */}
      <section id="features" className="mx-auto max-w-6xl px-6 py-20">
        <Reveal className="mx-auto max-w-2xl text-center">
          <h2 className="text-balance font-display text-3xl font-semibold tracking-tight sm:text-4xl">
            Everything you need to fill the room
          </h2>
          <p className="mt-3 text-muted-foreground">
            From the first invite to the day-of door, Gatherly handles the details so you can host.
          </p>
        </Reveal>

        <div className="mt-12 grid gap-4 md:grid-cols-3">
          <Reveal variant="left" className="md:col-span-2 md:row-span-2">
            <Tilt max={4} className="h-full">
              <article className="surface flex h-full flex-col p-6">
                <div className="flex items-center gap-2">
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand/10 text-brand">
                    <Users className="h-5 w-5" />
                  </span>
                  <h3 className="font-display text-xl font-semibold tracking-tight">
                    See every reply, live
                  </h3>
                </div>
                <p className="mt-2 max-w-md text-sm text-muted-foreground">
                  Yes, no, maybe, +1s and dietary needs — updating the moment a guest taps. An
                  automatic waitlist kicks in the instant you hit capacity.
                </p>
                <div className="mt-5 grow">
                  <GuestBoardMock />
                </div>
              </article>
            </Tilt>
          </Reveal>

          <Reveal as="article" variant="right" delay={80} className="surface p-6">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand/10 text-brand">
              <Bell className="h-5 w-5" />
            </span>
            <h3 className="mt-4 font-display text-lg font-semibold tracking-tight">
              Reminders that land
            </h3>
            <p className="mt-1.5 text-sm text-muted-foreground">
              Automatic nudges before the day, so nobody forgets to show up.
            </p>
          </Reveal>

          <Reveal as="article" variant="right" delay={160} className="surface p-6">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand/10 text-brand">
              <ClipboardCheck className="h-5 w-5" />
            </span>
            <h3 className="mt-4 font-display text-lg font-semibold tracking-tight">
              Door-ready check-in
            </h3>
            <p className="mt-1.5 text-sm text-muted-foreground">
              Tick guests off from any phone as they arrive — no clipboard.
            </p>
          </Reveal>
        </div>
      </section>

      {/* ── Showcase: invite ─────────────────────────────────── */}
      <section className="border-y border-border/70 bg-muted/30">
        <div className="mx-auto grid max-w-6xl items-center gap-12 px-6 py-20 lg:grid-cols-2">
          <Reveal variant="left">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand">
              The guest experience
            </span>
            <h2 className="mt-2 text-balance font-display text-3xl font-semibold tracking-tight sm:text-4xl">
              An invite they&apos;ll actually open
            </h2>
            <p className="mt-3 max-w-md text-muted-foreground">
              No logins, no clutter. Each guest lands on a clean, personal page — sets their RSVP,
              adds a +1, notes a dietary need, and drops it on their calendar in seconds.
            </p>
            <ul className="mt-6 space-y-2.5 text-sm">
              {["Private link per guest", "Add-to-calendar in one tap", "Works on any phone"].map(
                (item) => (
                  <li key={item} className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 shrink-0 text-success" /> {item}
                  </li>
                ),
              )}
            </ul>
          </Reveal>
          <Reveal variant="right" className="flex justify-center">
            <div className="relative">
              <span
                className="halo bg-brand/20"
                style={{ width: 260, height: 260, top: 20, left: 20 }}
              />
              <Tilt max={8}>
                <RsvpPhoneMock className="relative w-64 animate-float-slow" />
              </Tilt>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ── How it works (illustrated, draws in) ─────────────── */}
      <section id="how" className="mx-auto max-w-6xl px-6 py-20">
        <Reveal className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-3xl font-semibold tracking-tight sm:text-4xl">
            Live in three steps
          </h2>
          <p className="mt-3 text-muted-foreground">No setup call. No manual. Just your event.</p>
        </Reveal>
        <div className="mt-14 grid gap-6 md:grid-cols-3">
          {STEPS.map((step, i) => (
            <Reveal key={step.n} delay={i * 140} as="article" className="draw surface p-6 text-center">
              <div className="rounded-xl bg-muted/40 p-3">
                <step.Art />
              </div>
              <span className="mt-5 inline-block font-mono text-sm font-semibold text-brand">
                {step.n}
              </span>
              <h3 className="mt-1 font-display text-xl font-semibold tracking-tight">
                {step.title}
              </h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{step.body}</p>
            </Reveal>
          ))}
        </div>
      </section>

      {/* ── Feature grid ─────────────────────────────────────── */}
      <section className="border-t border-border/70 bg-muted/30">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <Reveal className="mx-auto max-w-2xl text-center">
            <h2 className="font-display text-3xl font-semibold tracking-tight sm:text-4xl">
              Built for hosts who sweat the details
            </h2>
            <p className="mt-3 text-muted-foreground">
              The small things that make an event feel effortless.
            </p>
          </Reveal>
          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((feature, i) => (
              <Reveal
                key={feature.title}
                delay={(i % 3) * 90}
                variant="up"
                as="article"
                className="surface group p-6 transition-all duration-300 hover:-translate-y-1 hover:border-brand/30 hover:shadow-lift"
              >
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand/10 text-brand transition-colors group-hover:bg-brand group-hover:text-white">
                  <feature.icon className="h-5 w-5" />
                </span>
                <h3 className="mt-4 font-display text-lg font-semibold tracking-tight">
                  {feature.title}
                </h3>
                <p className="mt-1.5 text-sm text-muted-foreground">{feature.body}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ── Gallery ──────────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <Reveal className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-3xl font-semibold tracking-tight sm:text-4xl">
            For every kind of gathering
          </h2>
          <p className="mt-3 text-muted-foreground">
            From a backyard birthday to a 300-seat conference — one tool, every occasion.
          </p>
        </Reveal>
        <div className="mt-12 grid grid-cols-2 gap-4 md:grid-cols-4">
          {GALLERY.map((g, i) => (
            <Reveal
              key={g.label}
              variant="scale"
              delay={i * 80}
              className="group relative overflow-hidden rounded-2xl"
            >
              {/* eslint-disable-next-line @next/next/no-img-element -- decorative Unsplash imagery, no domain allowlist needed */}
              <img
                src={unsplash(g.src)}
                alt={g.label}
                loading="lazy"
                referrerPolicy="no-referrer"
                className="aspect-[4/5] w-full object-cover transition-transform duration-500 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-foreground/30" />
              <span className="absolute bottom-3 left-3 rounded-full bg-background/85 px-3 py-1 text-xs font-semibold backdrop-blur">
                {g.label}
              </span>
            </Reveal>
          ))}
        </div>
      </section>

      {/* ── Testimonial ──────────────────────────────────────── */}
      <section className="border-y border-border/70 bg-muted/30">
        <div className="mx-auto max-w-3xl px-6 py-20 text-center">
          <Reveal variant="blur">
            <Quote className="mx-auto h-9 w-9 text-brand/30" />
            <p className="mt-5 text-balance font-display text-2xl font-medium leading-snug tracking-tight sm:text-3xl">
              “We ran our 250-person launch on Gatherly. Real-time RSVPs, an automatic waitlist, and
              door check-in that just worked. It made us look effortlessly organized.”
            </p>
            <div className="mt-7 flex items-center justify-center gap-3">
              {/* eslint-disable-next-line @next/next/no-img-element -- decorative Unsplash portrait */}
              <img
                src={unsplash("1438761681033-6461ffad8d80", 96)}
                alt="Elena Rossi"
                loading="lazy"
                referrerPolicy="no-referrer"
                className="h-11 w-11 rounded-full border object-cover"
              />
              <div className="text-left">
                <p className="text-sm font-semibold">Elena Rossi</p>
                <p className="text-xs text-muted-foreground">Head of Events, Northwind</p>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ── Pricing ──────────────────────────────────────────── */}
      <section id="pricing" className="mx-auto max-w-6xl px-6 py-20">
        <Reveal className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-3xl font-semibold tracking-tight sm:text-4xl">
            Start free. Upgrade when you grow.
          </h2>
          <p className="mt-3 text-muted-foreground">Simple pricing, no surprises.</p>
        </Reveal>
        <div className="mx-auto mt-12 grid max-w-3xl gap-6 sm:grid-cols-2">
          <Reveal variant="left" className="surface p-7">
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
          </Reveal>
          <Reveal
            variant="right"
            delay={100}
            className="relative rounded-2xl border-2 border-brand bg-card p-7 shadow-glow"
          >
            <span className="absolute -top-3 left-7 inline-flex items-center gap-1 rounded-full bg-primary px-3 py-1 text-xs font-semibold text-primary-foreground">
              <Sparkles className="h-3 w-3" /> Most popular
            </span>
            <p className="font-display text-lg font-semibold">Pro</p>
            <p className="mt-2">
              <span className="font-display text-4xl font-semibold tracking-tight">$12</span>
              <span className="text-muted-foreground"> / month</span>
            </p>
            <p className="mt-1 text-sm text-muted-foreground">For frequent &amp; professional hosts.</p>
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
          </Reveal>
        </div>
      </section>

      {/* ── FAQ ──────────────────────────────────────────────── */}
      <section id="faq" className="border-t border-border/70 bg-muted/30">
        <div className="mx-auto max-w-3xl px-6 py-20">
          <Reveal>
            <h2 className="text-center font-display text-3xl font-semibold tracking-tight sm:text-4xl">
              Questions, answered
            </h2>
          </Reveal>
          <Reveal delay={80} className="mt-10 divide-y divide-border/70 overflow-hidden rounded-2xl border bg-card">
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
          </Reveal>
        </div>
      </section>

      {/* ── Final CTA ────────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <Reveal variant="scale" className="relative overflow-hidden rounded-3xl border bg-card px-8 py-16 text-center shadow-soft">
          <div className="bg-dots pointer-events-none absolute inset-0 [mask-image:radial-gradient(ellipse_60%_80%_at_50%_50%,black,transparent)]" />
          <Confetti className="opacity-40" />
          <span className="halo bg-brand/20" style={{ width: 300, height: 300, top: -80, left: "30%" }} />
          <div className="relative">
            <h2 className="text-balance font-display text-3xl font-semibold tracking-tight sm:text-4xl">
              Your next event deserves a better RSVP.
            </h2>
            <p className="mx-auto mt-3 max-w-md text-muted-foreground">
              Join the hosts making it effortless to gather the people they love.
            </p>
            <Button asChild size="lg" className="mt-7 shadow-glow">
              <Link href="/signup">
                Get started — it&apos;s free <ArrowRight className="ml-1.5 h-4 w-4" />
              </Link>
            </Button>
            <p className="mt-3 text-xs text-muted-foreground">No credit card required.</p>
          </div>
        </Reveal>
      </section>

      <MarketingFooter />
    </div>
  );
}
