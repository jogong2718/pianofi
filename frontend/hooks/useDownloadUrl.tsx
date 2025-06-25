import { useState, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";

interface getDownloadResponse {
  jobId: string;
  status: string;
  download_url?: string;
  result_key?: string;
}

export function useDownloadUrl() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const supabase = createClient();

  const getDownloadUrl = useCallback(
    async (jobId: string) => {
      setLoading(true);
      setError(null);

      try {
        const {
          data: { session },
        } = await supabase.auth.getSession();

        if (!session?.access_token) {
          throw new Error("No authentication token found");
        }

        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
        const res = await fetch(`${backendUrl}/getDownload/${jobId}`, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });
        console.log("Fetching job details for jobId:", jobId);
        console.log(res);

        if (!res.ok) {
          throw new Error(`Get job request failed: ${res.statusText}`);
        }

        const data: getDownloadResponse = await res.json();

        console.log("Job details received:", data);

        // Check if job is completed and has download URL
        if (data.status !== "done" && data.status !== "completed") {
          throw new Error("Job is not completed yet");
        }

        if (!data.download_url) {
          throw new Error("Download URL not available");
        }

        return { download_url: data.download_url };
      } catch (err: any) {
        setError(err.message || "Unknown error");
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [supabase]
  );

  return {
    getDownloadUrl,
    loading,
    error,
  };
}
