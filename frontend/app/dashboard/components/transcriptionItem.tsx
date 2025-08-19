import { FC, useState } from "react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Download, MoreHorizontal, Trash2, Eye, Edit2, Check, X } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import TranscriptionStatusBadge from "./transcriptionStatusBadge";
import { useDeleteJob } from "@/hooks/useDeleteJob";
import { useUpdateJob } from "@/hooks/useUpdateJob";

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
  updateTranscriptionFilename: (jobId: string, newFilename: string) => void;
}

const TranscriptionItem: FC<TranscriptionItemProps> = ({
  transcription,
  onDownload,
  onClick,
  updateTranscriptionFilename,
}) => {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedName, setEditedName] = useState(transcription.filename || "");
  
  const { deleteJob, loading: deleteLoading } = useDeleteJob();
  const { updateJob, loading: updateLoading } = useUpdateJob();

  const handleDelete = async () => {
    await deleteJob(transcription.id);
    setShowDeleteDialog(false);
  };

  const handleEdit = () => {
    setIsEditing(true);
    setEditedName(transcription.filename || "");
  };

  const handleSave = async () => {
    if (editedName.trim() === "") {
      toast.error("Filename cannot be empty");
      return;
    }

    try {
      await updateJob({
        job_id: transcription.id,
        file_name: editedName.trim(),
      });
      
      // Instantly update UI
      updateTranscriptionFilename(transcription.id, editedName.trim());
      setIsEditing(false);
      
    } catch (error) {
      // Reset input on error
      setEditedName(transcription.filename || "");
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditedName(transcription.filename || "");
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSave();
    } else if (e.key === "Escape") {
      handleCancel();
    }
  };

  return (
    <>
      <div className="flex flex-col space-y-2 sm:flex-row sm:space-y-0 items-start sm:items-center justify-between p-4 border rounded-lg">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="min-w-4 min-h-4">
              <TranscriptionStatusBadge status={transcription.status} />
            </div>
            <div>
              {isEditing ? (
                <div className="flex items-center gap-2">
                  <Input
                    value={editedName}
                    onChange={(e) => setEditedName(e.target.value)}
                    onKeyDown={handleKeyPress}
                    className="text-base font-medium bg-gray-100 dark:bg-gray-800 border-none shadow-none outline-none focus:ring-0 focus:border-none focus:outline-none focus-visible:ring-0 focus-visible:ring-offset-0 p-0 m-0 h-6 max-w-72"
                    autoFocus
                    disabled={updateLoading}
                  />
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleSave}
                    disabled={updateLoading}
                    className="h-6 w-6 p-0"
                  >
                    <Check className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleCancel}
                    disabled={updateLoading}
                    className="h-6 w-6 p-0"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <p className="font-medium">{transcription.filename}</p>
              )}
              <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                <span>{transcription.duration}</span>
                <span>{transcription.size}</span>
                <span>{transcription.uploadedAt}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-4 ml-4 sm:ml-0">
          <div className="flex items-center space-x-2">
            <Badge
              variant={
                transcription.status === "completed"
                  ? "default"
                  : transcription.status === "processing"
                  ? "secondary"
                  : transcription.status === "failed"
                  ? "destructive"
                  : "outline" // For initialized/queued
              }
            >
              {transcription.status === "completed"
                ? "Completed"
                : transcription.status === "processing"
                ? "Processing"
                : transcription.status === "failed"
                ? "Failed"
                : transcription.status === "queued"
                ? "Queued"
                : "Initializing"}
            </Badge>
            {transcription.status === "processing" && (
              <div className="w-24">
                <Progress value={transcription.progress} />
              </div>
            )}
          </div>

          {transcription.status === "completed" && (
            <Button size="sm" variant="outline" onClick={onClick}>
              <Eye className="h-4 w-4" />
              <span className="hidden sm:inline">View Transcription</span>
              <span className="sm:hidden">View</span>
            </Button>
          )}

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={handleEdit} disabled={isEditing}>
                <Edit2 className="h-4 w-4 mr-2" />
                Edit
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => {
                  if (
                    !transcription.xml_download_url ||
                    transcription.xml_download_url === "pending" ||
                    transcription.xml_download_url === "error" ||
                    transcription.status === "missing"
                  ) {
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
                    toast.error("MusicXML file not available for download.");
                    return;
                  }
                  onDownload(transcription, "xml");
                }}
              >
                <Download className="h-4 w-4 mr-2" />
                XML
              </DropdownMenuItem>
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
