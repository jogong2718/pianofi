// hooks/useCreateJob.ts
import { useState } from "react";
import { createClient } from "@/lib/supabase/client";

interface CreateJobProps {
  jobId: string;
  fileKey: string;
}

interface CreateJobResponse {
  success: boolean;
}

export function useCreateJob() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const supabase = createClient();

  /**
   * callCreateJob({ jobId, fileKey })
   * └─ Sends POST /api/jobs
   * └─ Body = { jobId, fileKey }
   */
  async function callCreateJob({
    jobId,
    fileKey,
  }: CreateJobProps): Promise<CreateJobResponse> {
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
      const res = await fetch(`${backendUrl}/createJob`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ jobId, fileKey }),
      });

      if (!res.ok) {
        throw new Error(`Create-Job request failed: ${res.statusText}`);
      }

      const data: CreateJobResponse = await res.json();
      return data;
    } catch (err: any) {
      setError(err.message || "Unknown error");
      throw err;
    } finally {
      setLoading(false);
    }
  }

  return {
    callCreateJob,
    loading,
    error,
  };
}
