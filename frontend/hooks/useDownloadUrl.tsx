import { useState, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";

interface getDownloadResponse {
  jobId: string;
  status: string;
  midi_download_url?: string;
  xml_download_url?: string;
  pdf_download_url?: string;
  result_key?: string;
}

export function useDownloadUrl() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const supabase = createClient();

  const getDownloadUrl = useCallback(
    async (jobId: string, downloadType: string) => {
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
        let res: Response;
        if (downloadType === "midi") {
          res = await fetch(`${backendUrl}/getMidiDownload/${jobId}`, {
            method: "GET",
            headers: {
              Authorization: `Bearer ${session.access_token}`,
            },
          });
          console.log("Fetching MIDI download for jobId:", jobId);
        } else if (downloadType === "xml") {
          res = await fetch(`${backendUrl}/getXmlDownload/${jobId}`, {
            method: "GET",
            headers: { Authorization: `Bearer ${session.access_token}` },
          });
          console.log("Fetching XML download for jobId:", jobId);
        } else if (downloadType === "pdf") {
          res = await fetch(`${backendUrl}/getPdfDownload/${jobId}`, {
            method: "GET",
            headers: { Authorization: `Bearer ${session.access_token}` },
          });
          console.log("Fetching PDF download for jobId:", jobId);
        } else {
          throw new Error(`Invalid download type: ${downloadType}`);
        }

        if (!res.ok) {
          throw new Error(`Get job request failed: ${res.statusText}`);
        }

        const data: getDownloadResponse = await res.json();

        console.log("Job details received:", data);

        if (data.status === "missing") {
          console.log(
            "Download URL not available for this job (status: missing)"
          );
          return downloadType === "midi"
            ? { midi_download_url: undefined }
            : { xml_download_url: undefined };
        }

        // Check if job is completed and has download URL
        if (data.status !== "done" && data.status !== "completed") {
          throw new Error("Job is not completed yet");
        }

        if (!data.midi_download_url && !data.xml_download_url && !data.pdf_download_url) {
          throw new Error("Download URL not available");
        }

        if (downloadType === "midi") {
          return { midi_download_url: data.midi_download_url };
        } else if (downloadType === "xml") {
          return { xml_download_url: data.xml_download_url };
        } else if (downloadType === "pdf") {
          return { pdf_download_url: data.pdf_download_url };
        }
        // If we reach here, it means an invalid download type was specified
        throw new Error("Invalid download type specified");
      } catch (err: any) {
        setError(err.message || "Unknown error");
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [supabase]
  );

  return {
    getDownloadUrl,
    loading,
    error,
  };
}
