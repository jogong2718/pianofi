import { FC, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import TranscriptionItem from "./transcriptionItem";
import { useRouter } from "next/navigation";

interface TranscriptionsListProps {
  transcriptions: any[];
  updateTranscriptionFilename: (jobId: string, newFilename: string) => void;
}

const TranscriptionsList: FC<TranscriptionsListProps> = ({
  transcriptions,
  updateTranscriptionFilename,
}) => {
  const router = useRouter();
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
              onClick={() =>
                router.push(`/dashboard/transcription/${transcription.id}`)
              }
              updateTranscriptionFilename={updateTranscriptionFilename}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default TranscriptionsList;
