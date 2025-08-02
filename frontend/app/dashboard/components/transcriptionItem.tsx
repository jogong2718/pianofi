import { FC, useState } from "react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Download, MoreHorizontal, Trash2, Eye } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import TranscriptionStatusBadge from "./transcriptionStatusBadge";
import { useDeleteJob } from "@/hooks/useDeleteJob";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

import { toast } from "sonner";

interface TranscriptionItemProps {
  transcription: any;
  onDownload: (transcription: any, downloadType: string) => void;
  onClick: (transcription: any) => void;
}

const TranscriptionItem: FC<TranscriptionItemProps> = ({
  transcription,
  onDownload,
  onClick,
}) => {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const { deleteJob, loading: deleteLoading } = useDeleteJob();

  const handleDelete = async () => {
    await deleteJob(transcription.id);
    setShowDeleteDialog(false);
  };

  return (
    <>
      <div className="flex flex-col space-y-4 sm:flex-row sm:space-y-0 items-center justify-between p-4 border rounded-lg">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <TranscriptionStatusBadge status={transcription.status} />
            <div>
              <p className="font-medium">{transcription.filename}</p>
              <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                <span>{transcription.duration}</span>
                <span>{transcription.size}</span>
                <span>{transcription.uploadedAt}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Badge
              variant={
                transcription.status === "completed"
                  ? "default"
                  : transcription.status === "processing"
                  ? "secondary"
                  : "destructive"
              }
            >
              {transcription.status === "completed"
                ? "Completed"
                : transcription.status === "processing"
                ? "Processing"
                : "Failed"}
            </Badge>
            {transcription.status === "processing" && (
              <div className="w-24">
                <Progress value={transcription.progress} />
              </div>
            )}
          </div>

          {transcription.status === "completed" && (
            <Button size="sm" variant="outline" onClick={onClick}>
              <Eye className="h-4 w-4 mr-2" />
              View Transcription
            </Button>
          )}

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={() => {
                  if (
                    !transcription.xml_download_url ||
                    transcription.xml_download_url === "pending" ||
                    transcription.xml_download_url === "error" ||
                    transcription.status === "missing"
                  ) {
                    // Show a toast or message to the user
                    toast.error("Midi file not available for download.");
                    return;
                  }
                  onDownload(transcription, "midi");
                }}
              >
                <Download className="h-4 w-4 mr-2" />
                Midi
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  if (
                    !transcription.xml_download_url ||
                    transcription.xml_download_url === "pending" ||
                    transcription.xml_download_url === "error" ||
                    transcription.status === "missing"
                  ) {
                    // Show a toast or message to the user
                    toast.error("MusicXML file not available for download.");
                    return;
                  }
                  onDownload(transcription, "xml");
                }}
              >
                <Download className="h-4 w-4 mr-2" />
                XML
              </DropdownMenuItem>
              {/* <DropdownMenuItem>Reprocess</DropdownMenuItem> */}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-red-600"
                onClick={() => setShowDeleteDialog(true)}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Transcription</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{transcription.filename}"? This
              action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleteLoading}
              className="bg-red-600 hover:bg-red-700"
            >
              {deleteLoading ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

export default TranscriptionItem;
