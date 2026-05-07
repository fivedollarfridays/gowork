"use client";

/**
 * /auth/login — magic-link request surface (T22.10).
 *
 * State machine:
 *   idle       → email form, submit disabled until email is non-empty
 *   submitting → button shows spinner, input disabled
 *   success    → "check your email" confirmation (rendered for ALL outcomes
 *                so the API surface stays non-enumerating)
 */

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useMutation } from "@tanstack/react-query";
import { Loader2, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { requestMagicLink } from "@/lib/api/auth";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const mutation = useMutation({
    mutationFn: (addr: string) => requestMagicLink(addr),
    // Success vs error look identical to the user — the backend always
    // returns 202 Accepted, and we mirror that in the UI to avoid
    // leaking account existence.
    onSettled: () => setSubmitted(true),
  });

  const trimmed = email.trim();
  const canSubmit = trimmed.length > 0 && !mutation.isPending;

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!canSubmit) return;
    mutation.mutate(trimmed);
  }

  if (submitted) {
    return (
      <main className="min-h-screen flex items-center justify-center px-4 py-8">
        <Card className="w-full max-w-md text-center">
          <CardContent className="pt-6 space-y-4">
            <Mail className="mx-auto h-10 w-10 text-primary" aria-hidden />
            <p className="text-lg font-semibold">Check your email</p>
            <p className="text-sm text-muted-foreground">
              If an account exists for <span className="font-medium">{trimmed}</span>,
              we just sent a sign-in link. Open it on this device to finish
              signing in.
            </p>
            <p className="text-xs text-muted-foreground/70">
              The link expires in 15 minutes. You can close this tab.
            </p>
          </CardContent>
        </Card>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-1">
          <h1 className="text-3xl font-bold text-primary">Sign in to GoWork</h1>
          <p className="text-sm text-muted-foreground">
            We&apos;ll email you a one-time link. No password required.
          </p>
        </div>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Your email</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium">
                  Email address
                </label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  inputMode="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  disabled={mutation.isPending}
                />
              </div>
              <Button
                type="submit"
                disabled={!canSubmit}
                className="w-full min-h-11"
              >
                {mutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Sending...
                  </>
                ) : (
                  "Send magic link"
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-muted-foreground/70">
          By continuing you agree to our{" "}
          <Link href="/terms" className="underline">terms</Link> and{" "}
          <Link href="/privacy" className="underline">privacy policy</Link>.
        </p>
      </div>
    </main>
  );
}
