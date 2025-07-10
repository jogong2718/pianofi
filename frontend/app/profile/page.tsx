"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Music } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { ProfileSidebar } from "./components/profileSidebar";
import { ProfileSection } from "./components/profileSection";
import { BillingSection } from "./components/billingSection";
import { SettingsSection } from "./components/settingsSection";
import { SidebarSection, User } from "./types";

export default function ProfilePage() {
  const router = useRouter();
  const supabase = createClient();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState<SidebarSection>("profile");

  useEffect(() => {
    const getUser = async () => {
      const {
        data: { user },
        error,
      } = await supabase.auth.getUser();

      if (error || !user) {
        router.push("/login");
        return;
      }

      setUser(user);
      setLoading(false);
    };

    getUser();
  }, [router, supabase.auth]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Music className="h-8 w-8 text-primary mx-auto mb-4" />
          <p>Loading Profile...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const renderContent = () => {
    switch (activeSection) {
      case "profile":
        return <ProfileSection user={user} />;
      // case "billing":
      //   return <BillingSection />;
      case "settings":
        return <SettingsSection />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="flex h-16 items-center px-4 lg:px-6">
          <Button
            variant="ghost"
            onClick={() => router.push("/dashboard")}
            className="mr-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Button>
          <h1 className="text-xl font-semibold">Account Settings</h1>
        </div>
      </header>

      <div className="flex">
        <ProfileSidebar
          activeSection={activeSection}
          onSectionChange={setActiveSection}
        />
        <main className="flex-1 p-6">
          <div className="min-h-screen max-w-7xl">{renderContent()}</div>
        </main>
      </div>
    </div>
  );
}
