"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Music } from "lucide-react";
import { Header } from "@/components/ui/header";
import { toast } from "sonner";
import { createClient } from "@/lib/supabase/client";

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isRedirecting, setIsRedirecting] = useState(false);
  const supabase = createClient();

  const passwordsMatch = password === confirmPassword;

  useEffect(() => {
    // Check if we have the necessary tokens in the URL OR if we have a valid session
    const token_hash = searchParams.get("token_hash");
    const type = searchParams.get("type");

    // If we have token params, that's fine - user came directly or through redirect
    // If we don't have params, check if we have a valid session (user came through auth/confirm)
    if (!token_hash || type !== "recovery") {
      // Check if we have a valid session from auth/confirm
      supabase.auth.getSession().then(({ data: { session } }: { data: { session: any } }) => {
        if (!session) {
          toast.error("Invalid or missing reset token. Please request a new password reset.");
          router.push("/forgot-password");
        }
        // If we have a session, we can proceed - the form will handle password update
      });
    }
  }, [searchParams, router, supabase]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (isLoading) return;

    if (!passwordsMatch) {
      toast.error("Passwords do not match");
      return;
    }

    if (password.length < 6) {
      toast.error("Password must be at least 6 characters long");
      return;
    }

    setIsLoading(true);

    try {
      // Check if we already have a session (user came through auth/confirm)
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        // No session, check if we have token_hash in URL to verify
        const token_hash = searchParams.get("token_hash");
        const type = searchParams.get("type");

        if (!token_hash || type !== "recovery") {
          toast.error("Invalid or missing reset token. Please request a new password reset.");
          setIsLoading(false);
          router.push("/forgot-password");
          return;
        }

        // Need to verify the OTP first
        const { error: verifyError } = await supabase.auth.verifyOtp({
          type: "recovery",
          token_hash,
        });

        if (verifyError) {
          toast.error("Invalid or expired reset token: " + verifyError.message);
          setIsLoading(false);
          return;
        }
      }

      // Update the password (we have a valid session now)
      const { error: updateError } = await supabase.auth.updateUser({
        password: password,
      });

      if (updateError) {
        toast.error("Failed to update password: " + updateError.message);
      } else {
        toast.success("Password reset successfully! Redirecting to login...");
        setIsRedirecting(true);
        setTimeout(() => {
          router.push("/login");
        }, 2000);
      }
    } catch (error) {
      toast.error("An unexpected error occurred. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  if (isRedirecting) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Music className="h-12 w-12 text-primary mx-auto mb-4 animate-spin" />
          <p>Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 dark:bg-none dark:from-transparent dark:to-transparent dark:bg-background">
      <Header />

      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="flex items-center justify-center mb-8">
            <Link href="/" className="flex items-center">
              <Music className="h-8 w-8 text-primary" />
              <span className="ml-2 text-2xl font-bold">PianoFi</span>
            </Link>
          </div>

          <Card>
            <CardHeader className="space-y-1">
              <CardTitle className="text-2xl text-center">
                Reset password
              </CardTitle>
              <CardDescription className="text-center">
                Enter your new password below
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="password">New Password</Label>
                  <Input
                    name="password"
                    id="password"
                    type="password"
                    placeholder="Enter new password"
                    value={password}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                    required
                    minLength={6}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Confirm Password</Label>
                  <Input
                    name="confirmPassword"
                    id="confirmPassword"
                    type="password"
                    placeholder="Confirm new password"
                    value={confirmPassword}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setConfirmPassword(e.target.value)}
                    required
                    minLength={6}
                  />
                  {!passwordsMatch && confirmPassword && (
                    <p className="text-sm text-red-600">Passwords must match</p>
                  )}
                </div>
                <Button
                  type="submit"
                  className="w-full"
                  disabled={isLoading || !passwordsMatch}
                >
                  {isLoading ? "Resetting password..." : "Reset password"}
                </Button>
              </form>

              <div className="text-center text-sm">
                <Link href="/login" className="text-primary hover:underline">
                  Back to login
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 dark:bg-none dark:from-transparent dark:to-transparent dark:bg-background">
          <Header />
          <div className="flex min-h-screen items-center justify-center p-4">
            <div className="text-center">
              <Music className="h-8 w-8 text-primary mx-auto mb-4" />
              <p>Loading...</p>
            </div>
          </div>
        </div>
      }
    >
      <ResetPasswordContent />
    </Suspense>
  );
}
