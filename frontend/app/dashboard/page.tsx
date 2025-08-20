"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Music } from "lucide-react";
import { UpgradeModal } from "@/components/ui/upgradeModal";
import { createClient } from "@/lib/supabase/client";
import { useAuth } from "@/lib/AuthContext"; // Add this import

import { useTranscriptionManager } from "@/hooks/useTranscriptionManager";
import { useDownloadUrl } from "@/hooks/useDownloadUrl";
import { useGetUserJobs } from "@/hooks/useGetUserJobs";
import { useDashboardMetrics } from "@/hooks/useGetDashboardMetrics";

import DashboardHeader from "./components/dashboardHeader";
import MetricsCards from "./components/metricsCards";
import FileUploader from "./components/fileUploader";
import TranscriptionsList from "./components/transcriptionsList";

// Create a new component for the dashboard content
function DashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams(); // Now wrapped in Suspense
  const supabase = createClient();
  const { user, loading, signOut } = useAuth();
  const [activeTab, setActiveTab] = useState("upload");
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);

  const { getDownloadUrl } = useDownloadUrl();
  const { getUserJobs } = useGetUserJobs();
  const { metrics, loading: metricsLoading } = useDashboardMetrics();

  const {
    transcriptions,
    handleJobCompletion,
    updateTranscriptionStatus,
    addTranscription,
    initialLoading,
    updateTranscriptionFilename,
  } = useTranscriptionManager({
    getDownloadUrl,
    getUserJobs,
    user,
    supabase,
  });

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
      return;
    }

    // Handle email confirmation toast
    const confirmed = searchParams.get("confirmed");
    if (confirmed === "true") {
      toast.success("Email verified successfully!");
    }
  }, [user, loading, router, searchParams]);

  // Show loading while auth is being checked or transcriptions are loading
  if (loading || initialLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 dark:bg-none dark:from-transparent dark:to-transparent dark:bg-background flex items-center justify-center">
        <div className="text-center">
          <Music className="h-8 w-8 text-primary mx-auto mb-4" />
          <p>Loading recent transcriptions...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const handleLogout = async () => {
    try {
      await signOut();
    } catch (error: any) {
      toast.error("Logout failed: " + error.message);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 dark:bg-none dark:from-transparent dark:to-transparent dark:bg-background">
      <UpgradeModal
        open={showUpgradeModal}
        onOpenChange={setShowUpgradeModal}
      />

      <DashboardHeader
        user={user}
        onLogout={handleLogout}
        onUpgradeClick={() => setShowUpgradeModal(true)}
      />

      <div className="flex-1 space-y-4 p-4 lg:p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        </div>

        <MetricsCards metrics={metrics} loading={metricsLoading} />

        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="space-y-4"
        >
          <TabsList>
            <TabsTrigger value="upload">Upload</TabsTrigger>
            <TabsTrigger value="transcriptions">My Transcriptions</TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="space-y-4">
            <FileUploader
              metrics={metrics}
              metricsLoading={metricsLoading}
              onUpgradeRequired={() => setShowUpgradeModal(true)}
              onFileUploaded={(newTranscription) => {
                addTranscription(newTranscription);
                setActiveTab("transcriptions");
              }}
              user={user}
            />
          </TabsContent>

          <TabsContent value="transcriptions" className="space-y-4">
            <TranscriptionsList
              transcriptions={transcriptions}
              updateTranscriptionFilename={updateTranscriptionFilename}
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

// New main component with Suspense wrapper
export default function DashboardPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 dark:bg-none dark:from-transparent dark:to-transparent dark:bg-background flex items-center justify-center">
          <div className="text-center">
            <Music className="h-8 w-8 text-primary mx-auto mb-4" />
            <p>Loading dashboard...</p>
          </div>
        </div>
      }
    >
      <DashboardContent />
    </Suspense>
  );
}
