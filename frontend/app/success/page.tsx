"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CheckCircle, Music, ArrowRight } from "lucide-react";

function SuccessContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const session_id = searchParams.get("session_id");
    if (session_id) {
      setSessionId(session_id);
    } else {
      // Redirect to dashboard if no session ID
      router.push("/dashboard");
      return;
    }
    setLoading(false);
  }, [searchParams, router]);

  const handleGoToDashboard = () => {
    router.push("/dashboard");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Card className="text-center shadow-lg">
          <CardHeader className="pb-4">
            <div className="mx-auto w-16 h-16 bg-green-100 dark:bg-green-950/50 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
            </div>
            <CardTitle className="text-2xl font-bold text-green-700 dark:text-green-400">
              Payment Successful!
            </CardTitle>
            <CardDescription>
              Welcome to PianoFi! Your subscription is now active.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            <div className="rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-900 dark:bg-green-950/30">
              <div className="flex items-center justify-center space-x-2 mb-2">
                <Music className="w-5 h-5 text-green-600 dark:text-green-400" />
                <span className="font-semibold text-green-800 dark:text-green-300">
                  You're all set!
                </span>
              </div>
              <p className="text-sm text-green-700 dark:text-green-400">
                Start transcribing your favorite songs into piano sheet music
                right away.
              </p>
            </div>

            {sessionId && (
              <div className="rounded bg-muted p-2 text-xs text-muted-foreground">
                <span className="font-mono">
                  Session: {sessionId.slice(0, 20)}...
                </span>
              </div>
            )}

            <div className="space-y-3">
              <Button
                onClick={handleGoToDashboard}
                className="w-full"
                size="lg"
              >
                Go to Dashboard
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>

              <Button
                variant="outline"
                onClick={() => router.push("/")}
                className="w-full"
              >
                Back to Home
              </Button>
            </div>

            <div className="text-xs text-muted-foreground">
              <p>
                Need help? Contact us at{" "}
                <a
                  href="mailto:jonathan@pianofi.ca"
                  className="text-primary hover:underline"
                >
                  jonathan@pianofi.ca
                </a>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function SuccessPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      }
    >
      <SuccessContent />
    </Suspense>
  );
}
