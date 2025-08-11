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
import { createClient } from "@/lib/supabase/client";

function SuccessContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const supabase = createClient();

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
  }, [searchParams]);

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
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Card className="text-center shadow-lg">
          <CardHeader className="pb-4">
            <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <CardTitle className="text-2xl font-bold text-green-800">
              Payment Successful!
            </CardTitle>
            <CardDescription className="text-gray-600">
              Welcome to PianoFi! Your subscription is now active.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center justify-center space-x-2 mb-2">
                <Music className="w-5 h-5 text-green-600" />
                <span className="font-semibold text-green-800">
                  You're all set!
                </span>
              </div>
              <p className="text-sm text-green-700">
                Start transcribing your favorite songs into piano sheet music
                right away.
              </p>
            </div>

            {sessionId && (
              <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                <span className="font-mono">
                  Session: {sessionId.slice(0, 20)}...
                </span>
              </div>
            )}

            <div className="space-y-3">
              <Button
                onClick={handleGoToDashboard}
                className="w-full bg-green-600 hover:bg-green-700"
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

            <div className="text-xs text-gray-500">
              <p>
                Need help? Contact us at{" "}
                <a
                  href="mailto:support@pianofi.com"
                  className="text-blue-600 hover:underline"
                >
                  support@pianofi.com
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
