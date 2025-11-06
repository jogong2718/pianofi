"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { CreditCard, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "sonner";
import { sub } from "date-fns";
import { createClient } from "@/lib/supabase/client";

export function BillingSection() {
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
  const [cancelOption, setCancelOption] = useState<"period_end" | "immediate">(
    "period_end"
  );

  const [isLoading, setIsLoading] = useState(false);
  const supabase = createClient();

  // TODO: Fetch actual subscription data from API
  const [subscription, setSubscription] = useState({
    planName: "loading...",
    price: "loading...",
    status: "loading...",
    nextBillingDate: "loading...",
  });

  useEffect(() => {
    const fetchSubscription = async () => {
      try {
        const {
          data: { session },
        } = await supabase.auth.getSession();

        if (!session?.access_token) {
          throw new Error("No authentication token found");
        }

        const response = await fetch(`${backendUrl}/getSubscription`, {
          method: "GET",
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (response.ok) {
          const data = await response.json();

          const processedData = {
            planName: data.planName ?? "Free",
            price: data.price ?? "$0.00",
            status: data.status ?? "inactive",
            nextBillingDate: data.nextBillingDate ?? "N/A",
          };

          setSubscription(processedData);
        }
      } catch (error) {
        console.error("Error fetching subscription:", error);
        toast.error("Failed to fetch subscription");
      }
    };
    fetchSubscription();
  }, [backendUrl]);

  const handleupdateSubscription = async () => {
    setIsLoading(true);
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.access_token) {
        throw new Error("No authentication token found");
      }

      const response = await fetch(`${backendUrl}/cancelSubscription`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          cancelAtPeriodEnd: cancelOption === "period_end",
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to cancel subscription");
      }

      const data = await response.json();
      console.log("Subscription cancelled:", data);

      toast.success("Subscription cancelled successfully");
      setShowCancelDialog(false);
    } catch (error) {
      console.error("Error cancelling subscription:", error);
      toast.error("Failed to cancel subscription");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Billing & Subscription
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="rounded-lg border p-4">
            <h3 className="font-semibold mb-4">Current Subscription</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm text-muted-foreground">Plan</p>
                  <p className="font-semibold">{subscription.planName}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">Price</p>
                  <p className="font-semibold">{subscription.price}</p>
                </div>
              </div>

              <div className="flex justify-between items-center pt-2 border-t">
                <div>
                  <p className="text-sm text-muted-foreground">Status</p>
                  <p className="font-semibold capitalize">
                    {subscription.status}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">Next billing</p>
                  <p className="font-semibold">
                    {subscription.nextBillingDate}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => setShowCancelDialog(true)}
            >
              Cancel Subscription
            </Button>
          </div>
        </CardContent>
      </Card>

      <Dialog open={showCancelDialog} onOpenChange={setShowCancelDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Cancel Subscription</DialogTitle>
            <DialogDescription>
              Choose when you'd like to cancel your subscription.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <RadioGroup
              value={cancelOption}
              onValueChange={(value) =>
                setCancelOption(value as "period_end" | "immediate")
              }
            >
              <div className="flex items-start space-x-3 space-y-0 rounded-md border p-4">
                <RadioGroupItem value="period_end" id="period_end" />
                <div className="flex-1">
                  <Label
                    htmlFor="period_end"
                    className="font-semibold cursor-pointer"
                  >
                    Cancel at end of billing period
                  </Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    Keep your access until {subscription.nextBillingDate}, then
                    cancel.
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-3 space-y-0 rounded-md border p-4">
                <RadioGroupItem value="immediate" id="immediate" />
                <div className="flex-1">
                  <Label
                    htmlFor="immediate"
                    className="font-semibold cursor-pointer"
                  >
                    Cancel immediately
                  </Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    End your subscription right now. No refund for unused time.
                    Dunno why I made this an option but maybe you just hate us
                    that much lol
                  </p>
                </div>
              </div>
            </RadioGroup>

            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {cancelOption === "period_end"
                  ? "You'll continue to have access to premium features until your billing period ends."
                  : "You'll lose access to premium features immediately upon cancellation."}
              </AlertDescription>
            </Alert>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCancelDialog(false)}
              disabled={isLoading}
            >
              Keep Subscription
            </Button>
            <Button
              variant="destructive"
              onClick={handleupdateSubscription}
              disabled={isLoading}
            >
              {isLoading ? "Cancelling..." : "Confirm Cancellation"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
