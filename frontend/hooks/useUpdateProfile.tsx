import { useState } from "react";
import { createClient } from "@/lib/supabase/client";

interface CreateUrlProps {
  first_name: string;
  last_name: string;
}

interface UpdateProfileResponse {
  success: boolean;
  message: string;
  user?: Record<string, any>;
}

export function useUpdateProfile() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const supabase = createClient();

  /**
   * useUpdateProfile()
   * └─ Sends PUT /updateProfile (user_id, first_name, last_name)
   * └─ Returns { success, message, user }
   */
  async function callUploadProfile({
    first_name,
    last_name,
  }: CreateUrlProps): Promise<UpdateProfileResponse> {
    setLoading(true);
    setError(null);
    let errorMessage = "bruh, something went wrong";

    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.access_token) {
        throw new Error("No authentication token found");
      }

      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
      const res = await fetch(`${backendUrl}/updateProfile`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ first_name, last_name }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        if (errorData.detail) {
          errorMessage = errorData.detail; // This gets the real backend error
        }
        throw new Error(errorMessage);
      }

      const data: UpdateProfileResponse = await res.json();
      return data;
    } catch (err: any) {
      setError(err.message || "Unknown error");
      throw err;
    } finally {
      setLoading(false);
    }
  }

  return {
    callUploadProfile,
    loading,
    error,
  };
}
