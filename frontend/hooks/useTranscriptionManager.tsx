import { useState, useEffect, useRef } from "react";
import { toast } from "sonner";

type TranscriptionStatus = "initialized" | "queued" | "processing" | "completed" | "done" | "failed" | "error";

interface Transcription {
  id: string;
  filename: string; // You might want to store this in your backend
  status: TranscriptionStatus;
  progress: number;
  uploadedAt: string;
  duration: string; // You might want to store this in your backend
  size: string; // You might want to store this in your backend
  download_url?: string;
}

interface UseTranscriptionManagerProps {
  getDownloadUrl: (jobId: string) => Promise<{ download_url: string }>;
  getUserJobs?: () => Promise<any[]>;
  user?: any;
}

export function useTranscriptionManager({ getDownloadUrl, getUserJobs, user }: UseTranscriptionManagerProps) {
    const [transcriptions, setTranscriptions] = useState<Transcription[]>([]);
    const [initialLoading, setInitialLoading] = useState(true);

    const isFetchingRef = useRef(false);
  
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
                    console.error("Could not fetch jobs, continuing with empty list:", fetchError);
                    // Continue with empty jobs list instead of failing completely
                }
                console.log("Fetched jobs:", jobs);
                const transcriptionsList: Transcription[] = jobs.map((job) => ({
                    id: job.job_id,
                    filename: "N/A", // You might want to store this in your backend
                    status: mapBackendStatusToFrontend(job.status),
                    progress: mapStatusToProgress(job.status),
                    uploadedAt: new Date(job.created_at).toISOString().split("T")[0],
                    duration: "N/A", // You might want to store this in your backend
                    size: "N/A", // You might want to store this in your backend
                    download_url: job.status === 'done' && job.result_key ? 'pending' : undefined, // Will be fetched when needed
            }));
    
            setTranscriptions(transcriptionsList);
    
            // For completed jobs, fetch download URLs
            const completedJobs = transcriptionsList.filter(t => 
                t.status === 'completed' && t.download_url === 'pending'
              );
            for (const job of completedJobs) {
                try {
                    const { download_url } = await getDownloadUrl(job.id);
                    setTranscriptions(prev => 
                        prev.map(t => 
                        t.id === job.id 
                            ? { ...t, download_url } 
                            : t
                        )
                    );
                } catch (error) {
                    console.error(`Failed to get download URL for job ${job.id}:`, error);

                    setTranscriptions(prev => 
                        prev.map(t => 
                            t.id === job.id 
                                ? { ...t, download_url: 'error' } 
                                : t
                        )
                    );
                }

            }

        } catch (error) {
            console.error("Failed to load existing transcriptions:", error);
            toast.error("Failed to load your transcriptions");
        } finally {
            isFetchingRef.current = false;
            // setInitialLoading(false);
        }
    };
    
        loadExistingTranscriptions();
    }, [user]);

    const mapBackendStatusToFrontend = (backendStatus: string): TranscriptionStatus => {
        switch (backendStatus) {
            case 'done':
            return 'completed';
            case 'processing':
            return 'processing';
            case 'error':
            return 'failed';
            case 'queued':
            return 'queued';
            case 'initialized':
            return 'initialized';
            default:
            return 'initialized';
        }
        };

  const handleJobCompletion = async (jobId: string, resultKey: string) => {

    const existingJob = transcriptions.find(t => t.id === jobId);
    if (existingJob?.download_url === 'error') {
        console.log(`Skipping repeated download URL attempt for job ${jobId}`);
        return;
    }

    try {
      // Get download URL from backend
      const { download_url } = await getDownloadUrl(jobId);
      
      // Update transcription with download URL
      setTranscriptions((prev) =>
        prev.map((t) =>
          t.id === jobId
            ? {
                ...t,
                status: "completed" as const,
                progress: 100,
                download_url: download_url,
              }
            : t
        )
      );

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
                download_url: 'error',  // Mark as error
              }
            : t
        )
      );

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
    initialLoading,
  };
}