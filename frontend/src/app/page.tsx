"use client";

import Link from "next/link";
import { ClipboardList, Target, Map } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  ScrollReveal, StaggerContainer, StaggerItem,
  Typewriter, AnimatedCounter,
} from "@/lib/motion";

const FLOW_STEPS = [
  {
    icon: ClipboardList,
    title: "Assess",
    description: "Answer a few questions about your situation, barriers, and work history",
  },
  {
    icon: Target,
    title: "Match",
    description: "We match you with jobs, resources, and transit routes in Montgomery",
  },
  {
    icon: Map,
    title: "Plan",
    description: "Get a personalized action plan: what to do Monday morning",
  },
];

const STATS = [
  { value: 20.9, suffix: "%", decimals: 1, label: "Poverty Rate" },
  { value: 57.4, suffix: "%", decimals: 1, label: "Labor Participation" },
  { value: 36, suffix: "K+", decimals: 0, label: "Residents Served Area" },
];

export default function Home() {
  return (
    <main className="flex flex-col">
      {/* Hero */}
      <section className="flex flex-col items-center justify-center px-4 py-20 sm:py-28 text-center">
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-primary max-w-3xl">
          <Typewriter text="What's standing between you and a job?" />
        </h1>
        <ScrollReveal delay={0.2}>
          <p className="mt-4 text-lg sm:text-xl text-muted-foreground max-w-xl">
            MontGoWork is a workforce navigator built for Montgomery, Alabama.
            We help you overcome barriers and find your path to employment.
          </p>
        </ScrollReveal>
        <ScrollReveal delay={0.4}>
          <div className="mt-8 flex gap-4">
            <Button size="lg" asChild>
              <Link href="/assess">Get Your Plan</Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/credit">Check Credit</Link>
            </Button>
          </div>
        </ScrollReveal>
      </section>

      {/* How it works */}
      <section className="px-4 py-16 bg-muted/30">
        <div className="mx-auto max-w-4xl">
          <h2 className="text-2xl font-semibold text-center text-primary mb-10">
            How It Works
          </h2>
          <StaggerContainer className="grid gap-6 sm:grid-cols-3">
            {FLOW_STEPS.map((step, i) => {
              const Icon = step.icon;
              return (
                <StaggerItem key={step.title}>
                  <Card className="text-center">
                    <CardContent className="pt-6 space-y-3">
                      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-secondary/10">
                        <Icon className="h-6 w-6 text-secondary" />
                      </div>
                      <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        Step {i + 1}
                      </div>
                      <h3 className="text-lg font-semibold">{step.title}</h3>
                      <p className="text-sm text-muted-foreground">{step.description}</p>
                    </CardContent>
                  </Card>
                </StaggerItem>
              );
            })}
          </StaggerContainer>
        </div>
      </section>

      {/* Montgomery stats */}
      <section className="px-4 py-16">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-2xl font-semibold text-primary mb-2">
            Montgomery by the Numbers
          </h2>
          <p className="text-muted-foreground mb-10">
            Understanding the workforce landscape we&apos;re built to serve
          </p>
          <div className="grid gap-6 sm:grid-cols-3">
            {STATS.map((stat) => (
              <div key={stat.label} className="space-y-1">
                <div className="text-3xl font-bold text-secondary">
                  <AnimatedCounter to={stat.value} suffix={stat.suffix} decimals={stat.decimals} />
                </div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      <ScrollReveal>
        <section className="px-4 py-16 bg-primary text-primary-foreground text-center">
          <div className="mx-auto max-w-xl space-y-4">
            <h2 className="text-2xl font-semibold">Ready to get started?</h2>
            <p className="text-primary-foreground/80">
              It takes about 2 minutes. No account needed.
            </p>
            <Button size="lg" variant="secondary" asChild>
              <Link href="/assess">Start Your Assessment</Link>
            </Button>
          </div>
        </section>
      </ScrollReveal>
    </main>
  );
}
