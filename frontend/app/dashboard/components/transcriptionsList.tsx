import { FC } from "react";
import { toast } from "sonner";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import TranscriptionItem from "./transcriptionItem";
import { useRouter } from 'next/navigation';

interface TranscriptionsListProps {
  transcriptions: any[];
}

const TranscriptionsList: FC<TranscriptionsListProps> = ({
  transcriptions,
}) => {
  const router = useRouter();

  const handleDownload = async (transcription: any) => {
    if (!transcription.download_url) {
      console.error(
        "Download URL not available for transcription:",
        transcription
      );
      toast.error("Download URL not available");
      return;
    }

    try {
      // For S3 presigned URLs or external URLs, open in new tab to trigger download
      if (transcription.download_url.startsWith("http")) {
        window.open(transcription.download_url, "_blank");
      } else {
        // For local API endpoints, use fetch and create blob
        console.log("Downloading locally from:", transcription.download_url);
        const response = await fetch(transcription.download_url);

        if (!response.ok) {
          throw new Error(`Download failed: ${response.statusText}`);
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);

        // Create temporary link and trigger download
        const link = document.createElement("a");
        link.href = url;
        link.download = transcription.filename.replace(/\.[^/.]+$/, ".mid"); // Change extension to .mid
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Clean up the blob URL
        window.URL.revokeObjectURL(url);
      }

      toast.success("Download started successfully!");
    } catch (error) {
      console.error("Download failed:", error);
      toast.error(`Download failed: ${(error as Error).message}`);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Transcriptions</CardTitle>
        <CardDescription>
          View and download your transcribed sheet music
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {transcriptions.map((transcription) => (
            <TranscriptionItem
              key={transcription.id}
              transcription={transcription}
              onDownload={handleDownload}
              onClick={() => {
                router.push(`/dashboard/transcription/${transcription.id}`);
              }}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default TranscriptionsList;
