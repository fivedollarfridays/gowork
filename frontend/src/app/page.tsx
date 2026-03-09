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
      <section className="flex flex-col items-center justify-center px-4 py-12 sm:py-16 text-center">
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
            <Button size="lg" asChild className="transition-shadow duration-300 hover:shadow-[0_0_20px_rgba(45,149,150,0.4)]">
              <Link href="/assess">Get Your Plan</Link>
            </Button>
            <Button size="lg" variant="outline" asChild className="transition-shadow duration-300 hover:shadow-[0_0_16px_rgba(45,149,150,0.25)]">
              <Link href="/credit">Check Credit</Link>
            </Button>
          </div>
        </ScrollReveal>
      </section>

      {/* How it works */}
      <section className="px-4 py-10 bg-muted/30">
        <div className="mx-auto max-w-4xl">
          <h2 className="text-2xl font-semibold text-center text-primary mb-6">
            How It Works
          </h2>
          <StaggerContainer className="grid gap-6 sm:grid-cols-3">
            {FLOW_STEPS.map((step, i) => {
              const Icon = step.icon;
              return (
                <StaggerItem key={step.title}>
                  <Card className="group text-center hover:shadow-[0_0_24px_rgba(45,149,150,0.3)] hover:border-secondary/40 hover:-translate-y-1">
                    <CardContent className="pt-6 space-y-3">
                      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-secondary/10 transition-colors duration-300 group-hover:bg-secondary/20">
                        <Icon className="h-6 w-6 text-secondary transition-transform duration-300 group-hover:scale-110" />
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
      <section className="px-4 py-10">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-2xl font-semibold text-primary mb-2">
            Montgomery by the Numbers
          </h2>
          <p className="text-muted-foreground mb-6">
            Understanding the workforce landscape we&apos;re built to serve
          </p>
          <div className="grid gap-6 sm:grid-cols-3">
            {STATS.map((stat) => (
              <div
                key={stat.label}
                className="space-y-1 rounded-xl border border-white/20 bg-white/60 dark:bg-white/5 backdrop-blur-md p-6 transition-all duration-300 hover:shadow-[0_0_20px_rgba(45,149,150,0.25)] hover:border-secondary/30"
              >
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
        <section className="px-4 py-10 bg-primary text-primary-foreground text-center">
          <div className="mx-auto max-w-xl space-y-3">
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
