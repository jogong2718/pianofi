// hooks/useCreateJob.ts
import { useState } from "react";

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
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
      const res = await fetch(`${backendUrl}/createJob`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
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
