import { useState } from "react";
import { toast } from "sonner";
import { createClient } from "@/lib/supabase/client";

interface UpdateJobProps {
  job_id: string;
  file_name: string;
}

interface UpdateJobResponse {
  success: boolean;
  message: string;
}

export function useUpdateJob() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const supabase = createClient();

  const updateJob = async ({ job_id, file_name }: UpdateJobProps): Promise<UpdateJobResponse> => {
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
      const response = await fetch(`${backendUrl}/updateJob`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ job_id, file_name }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        const errorMessage = errorData.detail || `Update failed: ${response.statusText}`;
        throw new Error(errorMessage);
      }

      const result: UpdateJobResponse = await response.json();
      toast.success("Job updated successfully");
      return result;
    } catch (err: any) {
      const errorMessage = err.message || "Unknown error";
      setError(errorMessage);
      toast.error(`Update failed: ${errorMessage}`);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { updateJob, loading, error };
}
