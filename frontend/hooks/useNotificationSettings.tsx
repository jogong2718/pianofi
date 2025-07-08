import { useState, useEffect } from "react";
import { NotificationManager } from "@/lib/notifications";
import { toast } from "sonner";

export function useNotificationSettings() {
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [permission, setPermission] =
    useState<NotificationPermission>("default");

  useEffect(() => {
    if ("Notification" in window) {
      setPermission(Notification.permission);
    }

    const saved = localStorage.getItem("notifications-enabled");
    if (saved) {
      setNotificationsEnabled(JSON.parse(saved));
    }
  }, []);

  const toggleNotifications = async () => {
    if (!notificationsEnabled) {
      const granted = await NotificationManager.requestPermission();
      if (granted) {
        setNotificationsEnabled(true);
        setPermission("granted");
        localStorage.setItem("notifications-enabled", "true");
        toast.success("Notifications enabled!");
        return true;
      }
      return false;
    } else {
      setNotificationsEnabled(false);
      localStorage.setItem("notifications-enabled", "false");
      toast.info("Notifications disabled.");
      return true;
    }
  };

  return {
    notificationsEnabled,
    permission,
    toggleNotifications,
  };
}
