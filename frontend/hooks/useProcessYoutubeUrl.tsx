// hooks/useProcessYoutubeUrl.ts
import { useState } from "react";
import { createClient } from "@/lib/supabase/client";

interface ProcessYoutubeUrlProps {
  youtube_url: string;
  model: string;
  level: number;
}

interface ProcessYoutubeUrlResponse {
  jobId: string;
  fileKey: string;
  success: boolean;
}

export function useProcessYoutubeUrl() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const supabase = createClient();

  /**
   * callProcessYoutubeUrl({ youtube_url, model, level })
   * └─ Sends POST /processYoutubeUrl
   * └─ Body = { youtube_url, model, level }
   * └─ Returns { jobId, fileKey, success }
   */
  async function callProcessYoutubeUrl({
    youtube_url,
    model,
    level,
  }: ProcessYoutubeUrlProps): Promise<ProcessYoutubeUrlResponse> {
    console.log("callProcessYoutubeUrl started", { youtube_url, model, level });
    setLoading(true);
    setError(null);

    try {
      console.log("Getting session...");
      const {
        data: { session },
      } = await supabase.auth.getSession();
      console.log("Session obtained:", session ? "yes" : "no");

      if (!session?.access_token) {
        throw new Error("No authentication token found");
      }

      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
      console.log("Making fetch to:", `${backendUrl}/processYoutubeUrl`);
      const res = await fetch(`${backendUrl}/processYoutubeUrl`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ youtube_url, model, level }),
      });
      console.log("Response status:", res.status);

      if (!res.ok) {
        const errorData = await res.json().catch(() => null);
        throw new Error(
          errorData?.detail || `Process YouTube URL failed: ${res.statusText}`
        );
      }

      const data: ProcessYoutubeUrlResponse = await res.json();
      console.log("Success:", data);
      return data;
    } catch (err: any) {
      console.error("Error in callProcessYoutubeUrl:", err);
      setError(err.message || "Unknown error");
      throw err;
    } finally {
      console.log("callProcessYoutubeUrl finished");
      setLoading(false);
    }
  }

  return {
    callProcessYoutubeUrl,
    loading,
    error,
  };
}
