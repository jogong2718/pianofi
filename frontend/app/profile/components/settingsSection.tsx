"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Settings as SettingsIcon, Bell, Shield } from "lucide-react";
import { useNotificationSettings } from "@/hooks/useNotificationSettings";

export function SettingsSection() {
  const { notificationsEnabled, permission, toggleNotifications } =
    useNotificationSettings();

  const handleToggleNotifications = async () => {
    await toggleNotifications();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <SettingsIcon className="h-5 w-5" />
          App Settings
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <h3 className="font-semibold flex items-center gap-2">
            <Bell className="h-4 w-4" />
            Notifications
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Processing alerts</p>
                <p className="text-xs text-muted-foreground">
                  Get notified when transcriptions complete
                </p>
              </div>
              <Button
                variant={notificationsEnabled ? "default" : "outline"}
                size="sm"
                onClick={handleToggleNotifications}
                disabled={permission === "denied"}
              >
                {notificationsEnabled ? "Enabled" : "Enable"}
              </Button>
            </div>
          </div>
        </div>

        {/* <div className="space-y-4">
          <h3 className="font-semibold flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Privacy & Security
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Download my data</p>
                <p className="text-xs text-muted-foreground">
                  Export all your transcriptions
                </p>
              </div>
              <Button variant="outline" size="sm">
                Download
              </Button>
            </div>
          </div>
        </div> */}
      </CardContent>
    </Card>
  );
}
