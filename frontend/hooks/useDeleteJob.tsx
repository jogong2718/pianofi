import { useState } from "react";
import { toast } from "sonner";
import { createClient } from "@/lib/supabase/client";

export function useDeleteJob() {
  const [loading, setLoading] = useState(false);
  const supabase = createClient();

  const deleteJob = async (jobId: string) => {
    setLoading(true);
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.access_token) {
        throw new Error("No authentication token found");
      }

      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
      const response = await fetch(`${backendUrl}/deleteJob/${jobId}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Delete failed: ${response.statusText}`);
      }

      const result = await response.json();
      toast.success("Transcription deleted successfully");
      return result;
    } catch (error) {
      console.error("Delete failed:", error);
      toast.error(`Delete failed: ${(error as Error).message}`);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  return { deleteJob, loading };
}
