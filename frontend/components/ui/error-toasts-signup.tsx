"use client";

import { useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { toast } from "@/hooks/use-toast";

export function ErrorHandler() {
  const searchParams = useSearchParams();
  const error = searchParams.get("error");

  useEffect(() => {
    if (error) {
      const errorMessages = {
        missing_fields: "All fields are required",
        passwords_do_not_match: "Passwords do not match",
        invalid_email: "Please enter a valid email address",
        password_too_short: "Password must be at least 8 characters",
        unexpected_error: "An unexpected error occurred",
      };

      toast({
        title: "Signup Failed",
        description:
          errorMessages[error as keyof typeof errorMessages] ||
          decodeURIComponent(error),
        variant: "destructive",
      });
    }
  }, [error]);

  return null;
}
