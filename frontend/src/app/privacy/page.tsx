// COUNSEL REVIEW REQUIRED BEFORE PROD — this is a hackathon-grade placeholder
// authored fresh for the GoWork submission, NOT legally-vetted. Production
// rollout requires actual privacy-counsel review (GDPR Art. 13-14, CCPA § 1798,
// COPPA, plus the relevant state privacy statutes).
"use client";

import Link from "next/link";
import { TranslationProvider, useTranslation } from "@/hooks/useTranslation";

const LAST_UPDATED = "2026-04-24";

function PrivacyContent() {
  const { t, locale } = useTranslation();
  const isEs = locale === "es";

  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-12 sm:py-16">
      <header className="mb-8 space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-primary sm:text-4xl">
          {t("privacy.heading")}
        </h1>
        <p className="text-sm text-muted-foreground">
          {t("privacy.lastUpdated")}: {LAST_UPDATED}
        </p>
        <p className="rounded-md border border-warning bg-warning/10 px-4 py-3 text-sm text-warning-foreground">
          {t("privacy.counselNotice")}
        </p>
      </header>

      {isEs ? <SpanishPlaceholder /> : <EnglishBody t={t} />}

      <footer className="mt-12 border-t pt-6 text-sm text-muted-foreground">
        <p>
          {t("privacy.seeAlso")}{" "}
          <Link href="/terms" className="underline hover:text-foreground">
            {t("privacy.termsLink")}
          </Link>
          .
        </p>
      </footer>
    </main>
  );
}

function SpanishPlaceholder() {
  const { t } = useTranslation();
  return (
    <section className="prose prose-sm sm:prose-base max-w-none text-foreground">
      <p>{t("privacy.esPlaceholder")}</p>
    </section>
  );
}

function EnglishBody({ t }: { t: (key: string) => string }) {
  return (
    <article className="space-y-8 text-base leading-relaxed text-foreground">
      <Section heading={t("privacy.collect.heading")}>
        <p>{t("privacy.collect.intro")}</p>
        <ul className="ml-6 list-disc space-y-1">
          <li>
            <strong>Session content.</strong> Your assessment answers (work
            history, education, criminal-record disclosures, and barriers like
            transportation, childcare, or housing), your plan checklist
            updates, and any chat with our barrier-intel assistant. We tie
            this data to a random session id, not your name.
          </li>
          <li>
            <strong>Advisor notes.</strong> If you choose to work with a case
            manager, the notes they leave on your session.
          </li>
          <li>
            <strong>Email address.</strong> Only if you opt into appointment or
            check-in reminders. We use it to send those emails and nothing
            else.
          </li>
          <li>
            <strong>Technical metadata.</strong> Request timestamps, IP
            address, and audit rows. Audit rows store a hash of your session
            id, not the id itself.
          </li>
        </ul>
      </Section>

      <Section heading={t("privacy.purpose.heading")}>
        <ul className="ml-6 list-disc space-y-1">
          <li>Match you to jobs, training, and benefits in your area.</li>
          <li>Generate your resume and cover letter on demand.</li>
          <li>Surface benefits-cliff warnings before you accept a job.</li>
          <li>Let an advisor follow up if you opted into that flow.</li>
          <li>
            Compliance audit: we keep an immutable record of every export and
            delete action so we can prove the system honored your data
            rights.
          </li>
        </ul>
      </Section>

      <Section heading={t("privacy.audience.heading")}>
        <ul className="ml-6 list-disc space-y-1">
          <li>
            <strong>You.</strong> Always. One click on the export action sends
            you a ZIP of every row tied to your session.
          </li>
          <li>
            <strong>Your case-manager advisor (only if you have one).</strong>{" "}
            Advisors are scoped to one city and only see sessions in that
            city. They cannot search across cities.
          </li>
          <li>
            <strong>Our LLM providers.</strong> When we generate a resume or
            run barrier-intel, we send the relevant text to the language model
            provider. We strip your session id before sending; the provider
            sees the content but not which session it belongs to.
          </li>
          <li>
            <strong>Our email vendor (SendGrid).</strong> Only your email
            address and the reminder body. They cannot see your plan, your
            barriers, or your session.
          </li>
          <li>Nobody else.</li>
        </ul>
      </Section>

      <Section heading={t("privacy.processors.heading")}>
        <p>{t("privacy.processors.intro")}</p>
        <ul className="ml-6 list-disc space-y-1">
          <li>
            <strong>Anthropic</strong> (United States) — language-model API
            for resume generation and barrier-intel chat. Receives anonymized
            text.
          </li>
          <li>
            <strong>OpenAI</strong> (United States) — language-model API
            (alternate provider). Receives anonymized text.
          </li>
          <li>
            <strong>Google Gemini</strong> (United States) — language-model
            API (alternate provider). Receives anonymized text.
          </li>
          <li>
            <strong>SendGrid</strong> (United States) — transactional email
            delivery. Receives your email address and reminder content only.
          </li>
          <li>
            <strong>BrightData</strong> (United States) — job-listing
            aggregation. Receives generic job-search queries (city, role
            keywords); no personal data.
          </li>
        </ul>
      </Section>

      <Section heading={t("privacy.rights.heading")}>
        <p>{t("privacy.rights.intro")}</p>
        <ul className="ml-6 list-disc space-y-1">
          <li>
            <strong>See your data.</strong> Open your Daily Plan and use the
            export action. We package every row as a ZIP with both a JSON
            file and a human-readable summary.
          </li>
          <li>
            <strong>Correct your data.</strong> Edit your profile and
            assessment answers any time. Updates take effect immediately.
          </li>
          <li>
            <strong>Delete your data.</strong> One click for full delete; a
            per-section option for partial delete. Full delete cascades
            through every table that holds your session.
          </li>
          <li>
            <strong>Auto-delete.</strong> We automatically purge your data
            ninety (90) days after your session expires, even if you forget.
          </li>
        </ul>
        <p>
          Export and delete actions are available from the{" "}
          <Link href="/daily" className="underline hover:text-primary">
            Daily Plan
          </Link>{" "}
          page.
        </p>
      </Section>

      <Section heading={t("privacy.children.heading")}>
        <p>
          GoWork is built for adult workers. We do not knowingly collect
          data from anyone under 13. If you believe a child has used the
          service, contact us and we will delete the session.
        </p>
      </Section>

      <Section heading={t("privacy.california.heading")}>
        <p>
          California residents have the same rights described above
          (access, correction, deletion). The California Consumer Privacy Act
          (CCPA) also gives you the right to opt out of the &ldquo;sale&rdquo;
          of personal information. <strong>We do not sell your data.</strong>{" "}
          To make a do-not-sell request anyway, email the contact below and
          we will confirm in writing.
        </p>
      </Section>

      <Section heading={t("privacy.security.heading")}>
        <ul className="ml-6 list-disc space-y-1">
          <li>Audit logs reference hashed session ids, not raw ids.</li>
          <li>
            Sensitive actions (export, delete, unsubscribe) require signed,
            single-use tokens with short lifetimes.
          </li>
          <li>
            We run automated security scans on every deploy and hold an audit
            trail of every privacy-affecting action.
          </li>
          <li>
            We scope advisor accounts to a single city and rate-limit
            cross-session searches.
          </li>
        </ul>
      </Section>

      <Section heading={t("privacy.changes.heading")}>
        <p>
          When we change this policy we update the &ldquo;last updated&rdquo;
          date above. Active sessions that have opted into reminders will
          receive an email summarizing material changes.
        </p>
      </Section>

      <Section heading={t("privacy.contact.heading")}>
        <p>
          Questions, requests, or complaints:{" "}
          <a
            href="mailto:privacy@gowork.example"
            className="underline hover:text-primary"
          >
            privacy@gowork.example
          </a>
          . A production rollout will list a physical postal address per
          CAN-SPAM &sect; 5(a)(5) and applicable state privacy statutes.
        </p>
      </Section>
    </article>
  );
}

function Section({
  heading,
  children,
}: {
  heading: string;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-3">
      <h2 className="text-xl font-semibold text-primary sm:text-2xl">
        {heading}
      </h2>
      {children}
    </section>
  );
}

export default function PrivacyPage() {
  return (
    <TranslationProvider>
      <PrivacyContent />
    </TranslationProvider>
  );
}
