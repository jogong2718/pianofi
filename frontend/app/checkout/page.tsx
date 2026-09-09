"use client";

import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  Suspense,
} from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useTheme } from "next-themes";
import type { Appearance } from "@stripe/stripe-js";
import {
  CheckoutProvider,
  PaymentElement,
  useCheckout,
} from "@stripe/react-stripe-js";
import { getStripe } from "@/lib/utils";
import { createClient } from "@/lib/supabase/client";
import { Header } from "@/components/ui/header";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Music, ArrowLeft, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

const stripePromise = getStripe();

/**
 * Build a Stripe Elements Appearance object that mirrors the site's theme.
 * We use Stripe's prebuilt "night" theme as a base in dark mode and "stripe"
 * in light mode, then override the key color variables to match PianoFi.
 */
function buildAppearance(isDark: boolean): Appearance {
  return {
    theme: isDark ? "night" : "stripe",
    variables: isDark
      ? {
          colorPrimary: "#e6c98f",
          colorBackground: "#0b0b0c",
          colorText: "#f5f5f4",
          colorDanger: "#f87171",
          borderRadius: "8px",
          fontFamily: "system-ui, sans-serif",
        }
      : {
          colorPrimary: "#a97c2f",
          colorBackground: "#ffffff",
          colorText: "#1c1917",
          colorDanger: "#df1b41",
          borderRadius: "8px",
          fontFamily: "system-ui, sans-serif",
        },
  };
}

/** The actual payment form; must live inside <CheckoutProvider>. */
function CheckoutForm({ isDark }: { isDark: boolean }) {
  const checkout = useCheckout();
  const [isPaying, setIsPaying] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  // Dynamically re-theme the Stripe Element whenever the site theme flips.
  useEffect(() => {
    checkout.changeAppearance(buildAppearance(isDark));
  }, [isDark, checkout]);

  const handleConfirm = async () => {
    setIsPaying(true);
    setMessage(null);

    const result = await checkout.confirm();

    if (result.type === "error") {
      setMessage(result.error.message);
      setIsPaying(false);
    }
    // On success Stripe redirects to the session's return_url.
  };

  return (
    <div className="space-y-5">
      <PaymentElement options={{ layout: "tabs" }} />

      {message && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{message}</AlertDescription>
        </Alert>
      )}

      <Button
        className="w-full"
        size="lg"
        onClick={handleConfirm}
        disabled={isPaying}
      >
        {isPaying ? "Processing…" : "Subscribe"}
      </Button>
    </div>
  );
}

function CheckoutContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
  const supabase = useMemo(() => createClient(), []);
  const { resolvedTheme } = useTheme();

  const [mounted, setMounted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const priceId = searchParams.get("priceId");
  const isDark = resolvedTheme === "dark";

  // next-themes only knows the real theme after mount (avoids hydration flash).
  useEffect(() => setMounted(true), []);

  useEffect(() => {
    if (!priceId) {
      setError("No plan selected. Please choose a plan to continue.");
    }
  }, [priceId]);

  const fetchClientSecret = useCallback(async (): Promise<string> => {
    try {
      if (!priceId) {
        throw new Error("No plan selected.");
      }

      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.access_token) {
        throw new Error("You need to be signed in to check out.");
      }

      const response = await fetch(`${backendUrl}/createCheckoutSession`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ priceId, uiMode: "custom" }),
      });

      if (!response.ok) {
        // Surface the backend/Stripe error detail so failures aren't silent.
        let detail = `Checkout failed (HTTP ${response.status}).`;
        try {
          const body = await response.json();
          if (body?.detail) detail = body.detail;
        } catch {
          /* non-JSON error body */
        }
        throw new Error(detail);
      }

      const data = await response.json();
      if (!data.clientSecret) {
        throw new Error("Checkout could not be initialized (no client secret).");
      }
      return data.clientSecret as string;
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to start checkout.";
      setError(msg);
      throw e;
    }
  }, [priceId, backendUrl, supabase]);

  // Initial appearance passed to the provider (before any theme toggle).
  const appearance = useMemo(() => buildAppearance(isDark), [isDark]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted">
      <Header />
      <main className="mx-auto w-full max-w-2xl px-4 py-10 lg:py-16">
        <div className="mb-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push("/dashboard")}
            className="gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to dashboard
          </Button>
        </div>

        <Card className="shadow-lg">
          <CardHeader className="text-center">
            <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
              <Music className="h-7 w-7 text-primary" />
            </div>
            <CardTitle className="text-2xl font-bold">
              Complete your upgrade
            </CardTitle>
            <CardDescription>
              You're one step away from unlocking PianoFi's best models.
            </CardDescription>
          </CardHeader>

          <CardContent>
            {error ? (
              <div className="space-y-4">
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
                <Button
                  className="w-full"
                  onClick={() => router.push("/dashboard")}
                >
                  Back to dashboard
                </Button>
              </div>
            ) : !mounted ? (
              <div className="flex justify-center py-10">
                <Music className="h-8 w-8 animate-spin text-primary" />
              </div>
            ) : (
              <CheckoutProvider
                stripe={stripePromise}
                options={{
                  fetchClientSecret,
                  elementsOptions: { appearance },
                }}
              >
                <CheckoutForm isDark={isDark} />
              </CheckoutProvider>
            )}
          </CardContent>
        </Card>

        <p className="mt-6 text-center text-xs text-muted-foreground">
          Payments are securely processed by Stripe. Need help? Contact{" "}
          <a
            href="mailto:jonathan@pianofi.ca"
            className="text-primary hover:underline"
          >
            jonathan@pianofi.ca
          </a>
        </p>
      </main>
    </div>
  );
}

export default function CheckoutPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <Music className="h-10 w-10 animate-spin text-primary" />
        </div>
      }
    >
      <CheckoutContent />
    </Suspense>
  );
}
