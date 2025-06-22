import { useState } from "react";
import { createClient } from "@/lib/supabase/client";

interface GetJobResponse {
  jobId: string;
  status: string;
  downloadUrl?: string;
  // Add other fields from your getJob response schema as needed
}

export function useDownloadUrl() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const supabase = createClient();

  async function getDownloadUrl(jobId: string): Promise<{ downloadUrl: string }> {
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
      const res = await fetch(`${backendUrl}/getJob/${jobId}`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!res.ok) {
        throw new Error(`Get job request failed: ${res.statusText}`);
      }

      const data: GetJobResponse = await res.json();
      
      // Check if job is completed and has download URL
      if (data.status !== 'done' && data.status !== 'completed') {
        throw new Error("Job is not completed yet");
      }

      if (!data.downloadUrl) {
        throw new Error("Download URL not available");
      }

      return { downloadUrl: data.downloadUrl };
    } catch (err: any) {
      setError(err.message || "Unknown error");
      throw err;
    } finally {
      setLoading(false);
    }
  }

  return {
    getDownloadUrl,
    loading,
    error,
  };
}