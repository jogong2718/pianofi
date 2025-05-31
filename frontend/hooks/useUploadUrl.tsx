import { useState } from "react";

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
   * └─ Sends POST /api/upload-url (no body)
   * └─ Returns { uploadUrl, jobId, fileKey }
   */
  async function callUploadUrl(): Promise<UploadUrlResponse> {
    setLoading(true);
    setError(null);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
      const res = await fetch(`${backendUrl}/uploadUrl`, {
        method: "POST",
      });

      if (!res.ok) {
        throw new Error(`Upload-URL request failed: ${res.statusText}`);
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
