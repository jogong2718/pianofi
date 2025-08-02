"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CreditCard } from "lucide-react";

export function BillingSection() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CreditCard className="h-5 w-5" />
          Billing & Subscription
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="rounded-lg border p-4">
          <h3 className="font-semibold mb-2">Current Plan</h3>
          <div className="flex justify-between items-center">
            <div>
              <p className="text-sm text-muted-foreground">Pro Plan</p>
              <p className="text-lg font-semibold">$19.99/month</p>
            </div>
            <Button variant="outline">Upgrade Plan</Button>
          </div>
        </div>

        <div className="rounded-lg border p-4">
          <h3 className="font-semibold mb-2">Payment Method</h3>
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <CreditCard className="h-4 w-4" />
              <span className="text-sm">•••• •••• •••• 4242</span>
            </div>
            <Button variant="outline" size="sm">
              Update
            </Button>
          </div>
        </div>

        <div className="rounded-lg border p-4">
          <h3 className="font-semibold mb-2">Billing History</h3>
          <p className="text-sm text-muted-foreground mb-3">
            View and download your invoices
          </p>
          <Button variant="outline" size="sm">
            View History
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
