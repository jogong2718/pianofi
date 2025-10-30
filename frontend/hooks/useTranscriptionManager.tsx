import { useState, useEffect, useRef, useCallback } from "react";
import { toast } from "sonner";
import { NotificationManager } from "@/lib/notifications";

import type { RealtimePostgresChangesPayload } from "@supabase/supabase-js";

type TranscriptionStatus =
  | "initialized"
  | "queued"
  | "processing"
  | "completed"
  | "done"
  | "failed"
  | "error";

interface Transcription {
  id: string;
  filename: string;
  status: TranscriptionStatus;
  progress: number;
  uploadedAt: string;
  duration: string;
  size: string;
  midi_download_url?: string;
  xml_download_url?: string;
  pdf_download_url?: string;
}

interface UseTranscriptionManagerProps {
  getDownloadUrl: (
    jobId: string,
    downloadType: string
  ) => Promise<{ midi_download_url?: string; xml_download_url?: string; pdf_download_url?: string }>;
  getUserJobs?: () => Promise<any[]>;
  user?: any;
  supabase?: any; // Optional, if you need to use supabase directly
}

export function useTranscriptionManager({
  getDownloadUrl,
  getUserJobs,
  user,
  supabase,
}: UseTranscriptionManagerProps) {
  const [transcriptions, setTranscriptions] = useState<Transcription[]>([]);
  const [initialLoading, setInitialLoading] = useState(true);

  const isFetchingRef = useRef(false);

  const deleteTranscription = useCallback((jobId: string) => {
    setTranscriptions((prev) => prev.filter((t) => t.id !== jobId));
  }, []);

  const updateTranscriptionFilename = useCallback((jobId: string, newFilename: string) => {
    setTranscriptions((prev) => 
      prev.map((t) => 
        t.id === jobId 
          ? { ...t, filename: newFilename }
          : t
      )
    );
  }, []);

  const handleJobCompletion = useCallback(
    async (jobId: string, resultKey: string) => {
      let shouldSkip = false;

      const existingJob = transcriptions.find((t) => t.id === jobId);
      if (
        existingJob?.midi_download_url === "error" ||
        existingJob?.xml_download_url === "error" || 
        existingJob?.pdf_download_url === "error"
      ) {
        console.log(`Skipping repeated download URL attempt for job ${jobId}`);
        shouldSkip = true;
        return;
      }

      if (shouldSkip) return;

      try {
        // Get download URL from backend
        const { midi_download_url } = await getDownloadUrl(jobId, "midi");
        const { xml_download_url } = await getDownloadUrl(jobId, "xml");
        const { pdf_download_url } = await getDownloadUrl(jobId, "pdf");

        // Update transcription with download URL
        setTranscriptions((prev) => {
          const updatedTranscriptions = prev.map((t) =>
            t.id === jobId
              ? {
                  ...t,
                  status: "completed" as const,
                  progress: 100,
                  midi_download_url: midi_download_url,
                  xml_download_url: xml_download_url,
                  pdf_download_url: pdf_download_url,
                }
              : t
          );

          const notificationsEnabled =
            localStorage.getItem("notifications-enabled") === "true";
          const completedJob = updatedTranscriptions.find(
            (t) => t.id === jobId
          );
          if (notificationsEnabled && completedJob) {
            NotificationManager.showTranscriptionComplete(
              completedJob.filename
            );
          }

          return updatedTranscriptions;
        });

        toast.success("Transcription completed!");
      } catch (error) {
        console.error("Failed to get download URL:", error);

        setTranscriptions((prev) =>
          prev.map((t) =>
            t.id === jobId
              ? {
                  ...t,
                  status: "completed" as const,
                  progress: 100,
                  xml_download_url: "error", // Mark as error
                  midi_download_url: "error", // Mark as error
                  pdf_download_url: "error",
                }
              : t
          )
        );

        toast.error("Failed to complete transcription");
      }
    },
    [getDownloadUrl, transcriptions]
  );

  const updateTranscriptionStatus = useCallback(
    (
      jobId: string,
      status: string,
      file_duration: number,
      file_size: number
    ) => {
      const typedStatus = status as TranscriptionStatus;

      setTranscriptions((prev) => {
        const updatedTranscriptions = prev.map((t) =>
          t.id === jobId
            ? {
                ...t,
                status: typedStatus,
                progress: mapStatusToProgress(status),
                duration: file_duration
                  ? `${Math.round(file_duration)}s`
                  : "N/A",
                size: file_size
                  ? `${(file_size / (1024 * 1024)).toFixed(2)} MB`
                  : "N/A",
              }
            : t
        );

        // Handle notifications using the updated state
        if (status === "failed") {
          toast.error("Transcription failed");

          const notificationsEnabled =
            localStorage.getItem("notifications-enabled") === "true";
          const failedJob = updatedTranscriptions.find((t) => t.id === jobId);
          if (notificationsEnabled && failedJob) {
            NotificationManager.showTranscriptionFailed(failedJob.filename);
          }
        }

        return updatedTranscriptions;
      });
    },
    []
  );

  useEffect(() => {
    const loadExistingTranscriptions = async () => {
      if (isFetchingRef.current || !user || !getUserJobs) {
        setInitialLoading(false);
        return;
      }

      isFetchingRef.current = true;
      console.log("Loading existing transcriptions...");

      try {
        let jobs = [];
        try {
          jobs = await getUserJobs();
          console.log("Fetched jobs:", jobs);
        } catch (fetchError) {
          console.error(
            "Could not fetch jobs, continuing with empty list:",
            fetchError
          );
          // Continue with empty jobs list instead of failing completely
        }
        const transcriptionsList: Transcription[] = jobs.map((job) => ({
          id: job.job_id,
          filename: job.file_name || "Unknown File",
          status: mapBackendStatusToFrontend(job.status),
          progress: mapStatusToProgress(job.status),
          uploadedAt: new Date(job.created_at).toISOString().split("T")[0],
          duration: job.file_duration
            ? `${Math.round(job.file_duration)}s`
            : "N/A",
          size: job.file_size
            ? `${(job.file_size / (1024 * 1024)).toFixed(2)} MB`
            : "N/A",
          midi_download_url:
            job.status === "done" && job.midi_download_url
              ? job.midi_download_url
              : "pending",
          xml_download_url:
            job.status === "done" && job.xml_download_url
              ? job.xml_download_url
              : "pending",
            pdf_download_url:
            job.status === "done" && job.pdf_download_url
              ? job.pdf_download_url
              : "pending",
        }));

        setTranscriptions(transcriptionsList);

      } catch (error) {
        console.error("Failed to load existing transcriptions:", error);
        toast.error("Failed to load your transcriptions");
      } finally {
        isFetchingRef.current = false;
        setInitialLoading(false);
      }
    };

    loadExistingTranscriptions();
  }, [user]);

  useEffect(() => {
    if (!user || !supabase) return;

    const deviceId = localStorage.getItem("deviceId") || (() => {
      const id = Math.random().toString(36).substr(2, 9);
      localStorage.setItem("deviceId", id);
      return id;
    })();

    const uniqueChannelName = `job-changes-${user.id}-${deviceId}`;
    
    // Remove any existing channel with this name first
    const existingChannels = supabase.getChannels();
    existingChannels.forEach(ch => {
      if (ch.topic === uniqueChannelName) {
        supabase.removeChannel(ch);
      }
    });

    const channel = supabase
      .channel(uniqueChannelName, {
        config: {
          presence: { key: deviceId }
        }
      })
      .on(
        "postgres_changes",
        {
          event: "*",
          schema: "public",
          table: "jobs",
          filter: `user_id=eq.${user.id}`,
        },
        async (payload: RealtimePostgresChangesPayload<any>) => {
          console.log("Job change detected:", payload);

          if (
            payload.eventType === "UPDATE" ||
            payload.eventType === "INSERT"
          ) {
            const jobData = payload.new;

            if (jobData.status === "deleted") {
              deleteTranscription(jobData.job_id);
              return;
            }

            if (jobData.status === "done") {
              await handleJobCompletion(jobData.job_id, jobData.result_key);
            } else {
              updateTranscriptionStatus(
                jobData.job_id,
                jobData.status,
                jobData.file_duration ?? 0,
                jobData.file_size ?? 0
              );
            }
          }
        }
      )
      .subscribe((status: string, err?: Error) => {
        console.log("Subscription status:", status);

        if (err) console.error("Subscription error:", err);

        // Add reconnection logic for failed connections
        if (status === "CHANNEL_ERROR" || status === "TIMED_OUT") {
          console.log("Connection failed, will retry on next mount");
        }
      });

    return () => {
      console.log("Cleaning up channel:", uniqueChannelName);
      if (channel) {
        channel.unsubscribe();
        supabase.removeChannel(channel);
      }
    };
  }, [user?.id, supabase]);

  const mapBackendStatusToFrontend = (
    backendStatus: string
  ): TranscriptionStatus => {
    switch (backendStatus) {
      case "done":
        return "completed";
      case "processing":
        return "processing";
      case "error":
        return "failed";
      case "queued":
        return "queued";
      case "initialized":
        return "initialized";
      default:
        return "initialized";
    }
  };

  const mapStatusToProgress = (status: string): number => {
    switch (status) {
      case "initialized":
        return 0;
      case "queued":
        return 10;
      case "processing":
        return 50;
      case "completed":
      case "done":
        return 100;
      case "failed":
      case "error":
        return 0;
      default:
        return 0;
    }
  };

  const addTranscription = (transcription: Transcription) => {
    setTranscriptions((prev) => [transcription, ...prev]);
  };

  return {
    transcriptions,
    handleJobCompletion,
    updateTranscriptionStatus,
    addTranscription,
    initialLoading,
    deleteTranscription,
    updateTranscriptionFilename,
  };
}
