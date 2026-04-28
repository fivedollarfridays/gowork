// COUNSEL REVIEW REQUIRED BEFORE PROD — this is a hackathon-grade placeholder
// authored fresh for the GoWork submission, NOT legally-vetted boilerplate.
// Production rollout requires actual contract counsel to set governing law,
// arbitration terms, liability caps, and DMCA / safe-harbor language.
"use client";

import Link from "next/link";
import { TranslationProvider, useTranslation } from "@/hooks/useTranslation";

const LAST_UPDATED = "2026-04-24";

function TermsContent() {
  const { t, locale } = useTranslation();
  const isEs = locale === "es";

  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-12 sm:py-16">
      <header className="mb-8 space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-primary sm:text-4xl">
          {t("terms.heading")}
        </h1>
        <p className="text-sm text-muted-foreground">
          {t("terms.lastUpdated")}: {LAST_UPDATED}
        </p>
        <p className="rounded-md border border-warning bg-warning/10 px-4 py-3 text-sm text-warning-foreground">
          {t("terms.counselNotice")}
        </p>
      </header>

      {isEs ? <SpanishPlaceholder /> : <EnglishBody t={t} />}

      <footer className="mt-12 border-t pt-6 text-sm text-muted-foreground">
        <p>
          {t("terms.seeAlso")}{" "}
          <Link href="/privacy" className="underline hover:text-foreground">
            {t("terms.privacyLink")}
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
      <p>{t("terms.esPlaceholder")}</p>
    </section>
  );
}

function EnglishBody({ t }: { t: (key: string) => string }) {
  return (
    <article className="space-y-8 text-base leading-relaxed text-foreground">
      <Section heading={t("terms.eligibility.heading")}>
        <p>
          You must be 18 years or older and a resident of the United States to
          use the worker companion. Case managers using the advisor view must
          be authorized by their employing organization.
        </p>
      </Section>

      <Section heading={t("terms.service.heading")}>
        <p>
          GoWork is a workforce navigator: we help you assess barriers to
          employment, match against jobs and resources in your area, generate
          a resume and cover letter, and follow through on a personalized
          plan.
        </p>
        <p>
          GoWork is <strong>not</strong> legal advice, <strong>not</strong>{" "}
          a guarantee of employment, and <strong>not</strong> a substitute
          for a human case worker, attorney, or social worker. Treat what we
          surface as a starting point.
        </p>
      </Section>

      <Section heading={t("terms.account.heading")}>
        <p>
          GoWork does not use traditional accounts. Each session is
          identified by a random session token tied to your browser. The token
          is the access key to your data. Do not share your URL with anyone
          you do not want to see your plan; whoever holds the token can view,
          export, or delete the session.
        </p>
      </Section>

      <Section heading={t("terms.acceptable.heading")}>
        <p>You agree not to:</p>
        <ul className="ml-6 list-disc space-y-1">
          <li>Spam advisor channels or other workers.</li>
          <li>
            Impersonate another person&rsquo;s situation to game the matching
            engine, get someone else&rsquo;s benefits, or collect data on
            them.
          </li>
          <li>
            Attempt to access another session by guessing or scraping
            tokens.
          </li>
          <li>Use the service to commit fraud or harm anyone.</li>
        </ul>
        <p>
          We may suspend or terminate any session that we reasonably believe
          violates these rules.
        </p>
      </Section>

      <Section heading={t("terms.content.heading")}>
        <p>
          You keep ownership of everything you submit (your work history,
          notes, plan checklist updates, chat with our barrier-intel
          assistant, and any uploads). You grant us a non-exclusive,
          royalty-free license to use that content for the purposes described
          in our Privacy Policy: matching, generating your documents,
          compliance audit, and improving the service. We do not sell your
          content. We do not use your content to train third-party models.
        </p>
      </Section>

      <Section heading={t("terms.ai.heading")}>
        <p>
          Your resume, cover letter, and the suggestions surfaced in the
          plan checklist are generated with AI assistance. AI output may be
          inaccurate, out of date, or generic. <strong>You are responsible
          for reviewing every AI-generated artifact before you send or sign
          it.</strong> We make no warranty as to the accuracy of AI output.
          Always verify benefits-cliff math, eligibility rules, and any
          claim about a specific employer or program.
        </p>
      </Section>

      <Section heading={t("terms.termination.heading")}>
        <p>
          You can delete your session at any time from the{" "}
          <Link href="/daily" className="underline hover:text-primary">
            Daily Plan
          </Link>{" "}
          page (full delete or per-section). The Privacy Policy describes
          the cascade and the 90-day post-expiry sweep. We may terminate or
          restrict a session for fraud, abuse, or security reasons.
        </p>
      </Section>

      <Section heading={t("terms.disclaimers.heading")}>
        <p>
          The service is provided &ldquo;as is&rdquo; and &ldquo;as
          available.&rdquo; We make no warranties, express or implied,
          including any warranty of fitness for a particular purpose. We are
          not responsible for hiring outcomes, benefits decisions made by
          third parties, or actions taken by employers, agencies, or
          advisors based on information surfaced through the service.
        </p>
      </Section>

      <Section heading={t("terms.liability.heading")}>
        <p>
          To the fullest extent permitted by law, our total liability to you
          for any claim arising out of or relating to the service is limited
          to the fees you paid for the service in the twelve months before
          the claim. Because the service is currently free, that cap is
          $0.
        </p>
      </Section>

      <Section heading={t("terms.disputes.heading")}>
        <p>
          We prefer to resolve disputes informally. Email us first and we
          will try to resolve the issue within thirty (30) days. If a
          dispute cannot be resolved, you may bring a claim in small-claims
          court or, at your option, in binding arbitration. We do not impose
          mandatory arbitration. (Counsel will replace this section with the
          jurisdiction-specific dispute terms before production rollout.)
        </p>
      </Section>

      <Section heading={t("terms.law.heading")}>
        <p>
          Governing law is to be set by counsel before production rollout
          (placeholder: laws of the state of incorporation, excluding its
          conflict-of-laws rules).
        </p>
      </Section>

      <Section heading={t("terms.changes.heading")}>
        <p>
          We may update these terms. The &ldquo;last updated&rdquo; date
          above changes when we do. Material changes will be summarized to
          active sessions that opted into reminders.
        </p>
      </Section>

      <Section heading={t("terms.contact.heading")}>
        <p>
          Questions about these terms:{" "}
          <a
            href="mailto:legal@gowork.example"
            className="underline hover:text-primary"
          >
            legal@gowork.example
          </a>
          .
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

export default function TermsPage() {
  return (
    <TranslationProvider>
      <TermsContent />
    </TranslationProvider>
  );
}
