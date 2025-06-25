import { useState, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";

interface Job {
  job_id: string;
  status: string;
  created_at: string;
  result_key?: string;
  file_name?: string;
  file_size?: number;
  file_duration?: number;
}

export function useGetUserJobs() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const supabase = createClient();

  const getUserJobs = useCallback(async () => {
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
      const res = await fetch(`${backendUrl}/getUserJobs`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!res.ok) {
        throw new Error(`Get user jobs failed: ${res.statusText}`);
      }

      const jobs: Job[] = await res.json();
      return jobs;
    } catch (err: any) {
      setError(err.message || "Unknown error");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    getUserJobs,
    loading,
    error,
  };
}
