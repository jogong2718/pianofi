"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { AlertCircle, Home, Mail, RefreshCw } from "lucide-react";
import { Header } from "@/components/ui/header";

function ErrorContent() {
  const searchParams = useSearchParams();
  const message = searchParams.get("message");
  const type = searchParams.get("type") || "general";

  // Parse the error message to provide better user experience
  const getErrorDetails = (errorMessage: string | null) => {
    if (!errorMessage) {
      return {
        title: "Something went wrong",
        description: "An unexpected error occurred. Please try again.",
        suggestions: ["Go back to the homepage", "Try refreshing the page"],
      };
    }

    const lowerMessage = errorMessage.toLowerCase();

    if (lowerMessage.includes("email") && lowerMessage.includes("verify")) {
      return {
        title: "Email Verification Failed",
        description: errorMessage,
        suggestions: [
          "Check if you clicked the correct link from your email",
          "Request a new confirmation email",
          "Make sure the link hasn't expired",
        ],
      };
    }

    if (lowerMessage.includes("invalid") && lowerMessage.includes("link")) {
      return {
        title: "Invalid Link",
        description: "The confirmation link is invalid or has expired.",
        suggestions: [
          "Request a new confirmation email",
          "Make sure you're using the latest email",
          "Check if you're already verified and try logging in",
        ],
      };
    }

    if (lowerMessage.includes("token")) {
      return {
        title: "Authentication Error",
        description: errorMessage,
        suggestions: [
          "The link may have expired",
          "Try requesting a new confirmation email",
          "Contact support if the problem persists",
        ],
      };
    }

    return {
      title: "Error",
      description: errorMessage,
      suggestions: ["Try again", "Contact support if the problem persists"],
    };
  };

  const errorDetails = getErrorDetails(message);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 dark:bg-none dark:from-transparent dark:to-transparent dark:bg-background">
      <Header />

      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="w-full max-w-md">
          <Card>
            <CardHeader className="text-center space-y-4">
              <div className="flex justify-center">
                <AlertCircle className="h-16 w-16 text-destructive" />
              </div>
              <CardTitle className="text-2xl">{errorDetails.title}</CardTitle>
              <CardDescription className="text-base">
                {errorDetails.description}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {errorDetails.suggestions.length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-medium text-sm text-muted-foreground">
                    What you can try:
                  </h4>
                  <ul className="space-y-2">
                    {errorDetails.suggestions.map((suggestion, index) => (
                      <li
                        key={index}
                        className="flex items-start space-x-2 text-sm"
                      >
                        <span className="text-muted-foreground">•</span>
                        <span>{suggestion}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="space-y-3">
                <Button asChild className="w-full">
                  <Link href="/">
                    <Home className="mr-2 h-4 w-4" />
                    Go to Homepage
                  </Link>
                </Button>

                {type === "email_verification" ||
                message?.toLowerCase().includes("email") ? (
                  <Button asChild variant="outline" className="w-full">
                    <Link href="/signup">
                      <Mail className="mr-2 h-4 w-4" />
                      Request New Confirmation
                    </Link>
                  </Button>
                ) : (
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => window.location.reload()}
                  >
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Try Again
                  </Button>
                )}

                <div className="text-center">
                  <p className="text-sm text-muted-foreground">
                    Need help?{" "}
                    <Link
                      href="/contact"
                      className="text-primary hover:underline"
                    >
                      Contact Support
                    </Link>
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function ErrorPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 dark:bg-none dark:from-transparent dark:to-transparent dark:bg-background">
          <Header />
          <div className="flex min-h-screen items-center justify-center p-4">
            <div className="text-center">
              <AlertCircle className="h-8 w-8 text-destructive mx-auto mb-4" />
              <p>Loading...</p>
            </div>
          </div>
        </div>
      }
    >
      <ErrorContent />
    </Suspense>
  );
}
