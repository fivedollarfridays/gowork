"use client";

/**
 * T2.46 — Archived pre-Wall landing page.
 *
 * This is a verbatim copy of the W1-era `frontend/src/app/page.tsx`,
 * preserved at `/archive` so we can:
 *   1. Roll back to the pre-Wall hero via a one-line page.tsx swap
 *      if the W2 Wall has rendering issues on submission day.
 *   2. Show judges the "before" state for context.
 *
 * The route is NOT linked from the footer (per T2.46 + Honest
 * Uncertainty #6). Direct URL only. Updates to `/archive` should be
 * intentional — this file is the rollback artifact, not a living route.
 */

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ClipboardList, Target, Map } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  ScrollReveal, StaggerContainer, StaggerItem,
  Typewriter, AnimatedCounter,
} from "@/lib/motion";
import { useCityConfig } from "@/hooks/useCityConfig";
import { getCityStats } from "@/lib/city-stats";
import { useAssessmentComplete } from "../home-redirect";
import { t } from "@/lib/i18n";

const FLOW_STEP_ICONS = [ClipboardList, Target, Map] as const;
const FLOW_STEP_KEYS = ["Assess", "Match", "Plan"] as const;

export default function ArchivedHome() {
  const city = useCityConfig();
  const stats = getCityStats(city.state);
  const router = useRouter();
  const assessmentComplete = useAssessmentComplete();

  useEffect(() => {
    if (assessmentComplete) {
      router.replace("/daily");
    }
  }, [assessmentComplete, router]);

  const flowSteps = [
    {
      icon: FLOW_STEP_ICONS[0],
      title: t("home.stepAssessTitle"),
      description: t("home.stepAssessDesc"),
    },
    {
      icon: FLOW_STEP_ICONS[1],
      title: t("home.stepMatchTitle"),
      description: t("home.stepMatchDesc"),
    },
    {
      icon: FLOW_STEP_ICONS[2],
      title: t("home.stepPlanTitle"),
      description: t("home.stepPlanDesc"),
    },
  ];

  const STATS = [
    { value: stats.povertyRate, suffix: "%", decimals: 1, label: t("home.statPoverty") },
    { value: stats.laborParticipation, suffix: "%", decimals: 1, label: t("home.statLabor") },
    { value: stats.populationValue, suffix: stats.populationLabel.replace(String(stats.populationValue), ""), decimals: 0, label: stats.populationDesc },
  ];

  return (
    <main className="flex flex-col">
      {/* Hero */}
      <section className="flex flex-col items-center justify-center px-4 py-12 sm:py-16 text-center">
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-primary max-w-3xl">
          <Typewriter text={t("home.heroQuestion")} />
        </h1>
        <ScrollReveal delay={0.2}>
          <p className="mt-4 text-lg sm:text-xl text-muted-foreground max-w-xl">
            {t("home.heroBlurb")}
          </p>
        </ScrollReveal>
        <ScrollReveal delay={0.4}>
          <div className="mt-8 flex gap-4">
            <Button size="lg" asChild className="transition-shadow duration-300 hover:shadow-[0_0_20px_rgba(45,149,150,0.4)]">
              <Link href="/assess">{t("home.ctaPlan")}</Link>
            </Button>
            <Button size="lg" variant="outline" asChild className="transition-shadow duration-300 hover:shadow-[0_0_16px_rgba(45,149,150,0.25)]">
              <Link href="/credit">{t("home.ctaCredit")}</Link>
            </Button>
          </div>
        </ScrollReveal>
      </section>

      {/* How it works */}
      <section className="px-4 py-10 bg-muted/30">
        <div className="mx-auto max-w-4xl">
          <h2 className="text-2xl font-semibold text-center text-primary mb-6">
            {t("home.howHeading")}
          </h2>
          <StaggerContainer className="grid gap-6 sm:grid-cols-3">
            {flowSteps.map((step, i) => {
              const Icon = step.icon;
              return (
                <StaggerItem key={FLOW_STEP_KEYS[i]}>
                  <Card className="group text-center hover:shadow-[0_0_24px_rgba(45,149,150,0.3)] hover:border-secondary/40 hover:-translate-y-1">
                    <CardContent className="pt-6 space-y-3">
                      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-secondary/10 transition-colors duration-300 group-hover:bg-secondary/20">
                        <Icon className="h-6 w-6 text-secondary transition-transform duration-300 group-hover:scale-110" />
                      </div>
                      <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        {t("home.stepLabel")} {i + 1}
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

      {/* City stats — powered by city config */}
      <section className="px-4 py-10">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-2xl font-semibold text-primary mb-2">
            {t("home.numbersHeading")}
          </h2>
          <p className="text-muted-foreground mb-6">
            {t("home.numbersSubtitlePrefix")} {stats.cityName}
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
            <h2 className="text-2xl font-semibold">{t("home.bottomCtaTitle")}</h2>
            <p className="text-primary-foreground/80">
              {t("home.bottomCtaBody")}
            </p>
            <Button size="lg" variant="secondary" asChild>
              <Link href="/assess">{t("home.bottomCtaButton")}</Link>
            </Button>
          </div>
        </section>
      </ScrollReveal>
    </main>
  );
}
