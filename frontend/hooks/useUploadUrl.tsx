import { useState } from "react";

interface CreateUrlProps {
  user_id: string;
  file_name: string;
  file_size: number;
  content_type: string;
}

interface UploadUrlResponse {
  uploadUrl: string;
  jobId: string;
  fileKey: string;
}

export function useUploadUrl() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * callUploadUrl()
   * └─ Sends POST /api/upload-url (user_id)
   * └─ Returns { uploadUrl, jobId, fileKey }
   */
  async function callUploadUrl({
    user_id,
    file_name,
    file_size,
    content_type,
  }: CreateUrlProps): Promise<UploadUrlResponse> {
    setLoading(true);
    setError(null);
    let errorMessage = "bruh, something went wrong";
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
      const res = await fetch(`${backendUrl}/uploadUrl`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ user_id, file_name, file_size, content_type }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        if (errorData.detail) {
          errorMessage = errorData.detail; // This gets the real backend error
        }
        throw new Error(errorMessage);
      }

      const data: UploadUrlResponse = await res.json();
      return data;
    } catch (err: any) {
      setError(err.message || "Unknown error");
      throw err;
    } finally {
      setLoading(false);
    }
  }

  return {
    callUploadUrl,
    loading,
    error,
  };
}
