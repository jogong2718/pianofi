import { useState } from "react";
import { toast } from "sonner";

type TranscriptionStatus = "initialized" | "queued" | "processing" | "completed" | "done" | "failed" | "error";

interface Transcription {
  id: string;
  filename: string;
  status: TranscriptionStatus;
  progress: number;
  uploadedAt: string;
  duration: string;
  size: string;
  downloadUrl?: string;
}

interface UseTranscriptionManagerProps {
  getDownloadUrl: (jobId: string) => Promise<{ downloadUrl: string }>;
}

export function useTranscriptionManager({ getDownloadUrl }: UseTranscriptionManagerProps) {
  const [transcriptions, setTranscriptions] = useState<Transcription[]>([
    {
        id: "1",
        filename: "bohemian-rhapsody.mp3",
        status: "completed",
        progress: 100,
        uploadedAt: "2024-01-15",
        duration: "5:55",
        size: "8.2 MB",
      },
      {
        id: "2",
        filename: "moonlight-sonata.wav",
        status: "processing",
        progress: 65,
        uploadedAt: "2024-01-15",
        duration: "3:20",
        size: "12.1 MB",
      },
      {
        id: "3",
        filename: "imagine.mp3",
        status: "completed",
        progress: 100,
        uploadedAt: "2024-01-14",
        duration: "3:03",
        size: "4.8 MB",
      },
  ]);

  const handleJobCompletion = async (jobId: string, resultKey: string) => {
    try {
      // Get download URL from backend
      const { downloadUrl } = await getDownloadUrl(jobId);
      
      // Update transcription with download URL
      setTranscriptions((prev) =>
        prev.map((t) =>
          t.id === jobId
            ? {
                ...t,
                status: "completed" as const,
                progress: 100,
                downloadUrl: downloadUrl,
              }
            : t
        )
      );

      toast.success("Transcription completed!");
    } catch (error) {
      console.error("Failed to get download URL:", error);
      updateTranscriptionStatus(jobId, "failed");
      toast.error("Failed to complete transcription");
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

  const updateTranscriptionStatus = (jobId: string, status: string) => {
    const typedStatus = status as TranscriptionStatus;
    setTranscriptions((prev) =>
        prev.map((t) =>
          t.id === jobId
            ? {
                ...t,
                status: typedStatus,
                progress: mapStatusToProgress(status),
              }
            : t
        )
      );

    if (status === "failed") {
      toast.error("Transcription failed");
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
  };
}