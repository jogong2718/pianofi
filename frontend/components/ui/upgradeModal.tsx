"use client";

import React, { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

/**
 * Stripe price IDs are mode-specific: a price created in test mode does not
 * exist in live mode (and vice versa). Keep it in the environment so each
 * deployment supplies its own.
 *
 * The fallback is the LIVE price, so production keeps working even if the env
 * var isn't set. Local/test environments override it in `frontend/.env.local`
 * with the test-mode price.
 */
const LAUNCH_PRICE_ID =
  process.env.NEXT_PUBLIC_LAUNCH_PRICE_ID || "price_1SQY6fBORHHlKrvYfRPevIWq";

interface UpgradeModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function UpgradeModal({ open, onOpenChange }: UpgradeModalProps) {
  const router = useRouter();
  const modalRef = useRef<HTMLDivElement>(null);

  if (!open) return null;

  const handleCheckout = (priceId: string) => {
    // Navigate to our themed in-app checkout page. The page itself creates the
    // embedded Stripe Checkout session and renders it inside our own layout.
    onOpenChange(false);
    router.push(`/checkout?priceId=${encodeURIComponent(priceId)}`);
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
      onOpenChange(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onMouseDown={handleBackdropClick}
    >
      <div
        ref={modalRef}
        className="bg-background text-foreground border border-border rounded-lg shadow-lg p-4 max-w-2xl w-full"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h2 className="text-lg font-bold mb-4 text-center">Choose Your Plan</h2>
        <div className="mx-auto grid grid-cols-1 gap-4 sm:grid-cols-1 mb-6">
          <Card className="flex flex-col h-full">
            <CardHeader>
              <CardTitle>Starter</CardTitle>
              <CardDescription>Perfect for trying out PianoFi</CardDescription>
              <div className="flex items-baseline gap-3">
                <div className="text-3xl font-bold text-primary">
                  $4.99
                  <span className="text-sm font-normal ml-1">/month</span>
                </div>
                <div className="text-sm text-muted-foreground line-through opacity-80">
                  $29
                </div>
                <Badge variant="secondary" className="text-sm">
                  Save $24.01!
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
              <ul className="space-y-2 text-sm flex-1">
                <li>
                  • Access to the most advanced SOTA transcription models and
                  access to our newest and best models when available!
                </li>
                <li>• 100 transcriptions per month</li>
              </ul>
              <Button
                onClick={() => handleCheckout(LAUNCH_PRICE_ID)}
                className="w-full mt-6"
              >
                Get Started
              </Button>
            </CardContent>
          </Card>
          {/* 
          <Card className="border-primary flex flex-col h-full">
            <CardHeader>
              <Badge className="w-fit">Most Popular</Badge>
              <CardTitle>Pro</CardTitle>
              <CardDescription>
                For serious musicians and teachers
              </CardDescription>
              <div className="text-3xl font-bold">
                $29<span className="text-sm font-normal">/month</span>
              </div>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
              <ul className="space-y-2 text-sm flex-1">
                <li>• 100 transcriptions per month</li>
                <li>• Up to 10 minutes per file</li>
                <li>• PDF + MusicXML downloads</li>
                <li>• Priority support</li>
                <li>• Batch processing</li>
              </ul>
              <Button
                onClick={() => handleCheckout("price_1RgbvaBHhIoAIsYdK7GAZW7h")}
                className="w-full mt-6"
              >
                Get Started
              </Button>
            </CardContent>
          </Card>
          <Card className="flex flex-col h-full">
            <CardHeader>
              <CardTitle>Enterprise</CardTitle>
              <CardDescription>For music schools and studios</CardDescription>
              <div className="text-3xl font-bold">
                $99<span className="text-sm font-normal">/month</span>
              </div>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
              <ul className="space-y-2 text-sm flex-1">
                <li>• Unlimited transcriptions</li>
                <li>• No file length limits</li>
                <li>• All formats included</li>
                <li>• Dedicated support</li>
                <li>• API access</li>
              </ul>
              <Button
                onClick={() => handleNavigation("/contact")}
                className="w-full mt-6"
              >
                Contact Sales
              </Button>
            </CardContent> */}
          {/* </Card> */}
        </div>
        <div className="flex justify-end">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}
