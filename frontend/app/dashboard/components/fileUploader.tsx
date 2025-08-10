import { FC, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Upload } from "lucide-react";
import { useUploadUrl } from "@/hooks/useUploadUrl";
import { useCreateJob } from "@/hooks/useCreateJob";
import { uploadToS3 } from "@/lib/utils";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";

interface FileUploaderProps {
  metrics: any;
  metricsLoading: boolean;
  onUpgradeRequired: () => void;
  onFileUploaded: (transcription: any) => void;
  user: any;
}

const FileUploader: FC<FileUploaderProps> = ({
  metrics,
  metricsLoading,
  onUpgradeRequired,
  onFileUploaded,
  user,
}) => {
  const [dragActive, setDragActive] = useState(false);

  const { callUploadUrl, loading: loadingUploadUrl } = useUploadUrl();

  const { callCreateJob, loading: loadingCreateJob } = useCreateJob();

  const [selectedModel, setSelectedModel] = useState<"amt" | "picogen">("amt");
  const [selectedLevel, setSelectedLevel] = useState<1 | 2 | 3>(2);
  const levelsDisabled = selectedModel === "picogen";

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const validateFile = (file: File): string | null => {
    if (!file) {
      return "No file selected";
    }

    const allowedTypes = ["audio/mpeg", "audio/wav", "audio/flac"];
    if (!allowedTypes.includes(file.type)) {
      return "Unsupported file type. Please upload MP3, WAV, or FLAC.";
    }

    const maxSize = 10 * 1024 * 1024; // 10MB in bytes
    if (file.size > maxSize) {
      return "File too large. Maximum size is 10MB.";
    }

    const allowedExtensions = [".mp3", ".wav", ".flac"];
    const hasValidExtension = allowedExtensions.some((ext) =>
      file.name.toLowerCase().endsWith(ext)
    );
    if (!hasValidExtension) {
      return "Invalid file extension. Please use .mp3, .wav, or .flac files.";
    }

    return null; // Valid file
  };

  const handleFiles = async (files: FileList) => {
    if (!user) return;

    if (metricsLoading) {
      toast.error("Please wait while we check your subscription limits...");
      return;
    }

    if (
      metrics?.transcriptions_left !== undefined &&
      metrics.transcriptions_left !== null &&
      metrics.transcriptions_left <= 0
    ) {
      toast.error(
        "You have reached your monthly transcription limit. Please upgrade your plan."
      );
      onUpgradeRequired();
      return;
    }

    if (
      metrics?.transcriptions_left !== null &&
      metrics?.transcriptions_left !== undefined &&
      metrics?.transcriptions_left <= 2
    ) {
      toast.warning(
        `Only ${metrics.transcriptions_left} transcription${
          metrics.transcriptions_left === 1 ? "" : "s"
        } left this month.`
      );
    }

    const file = files[0];

    // Validate file type and size
    const validationError = validateFile(file);
    if (validationError) {
      toast.error(validationError);
      return;
    }

    try {
      // 1) Get pre-signed upload URL + jobId + fileKey from backend
      const {
        uploadUrl,
        jobId: newJobId,
        fileKey,
      } = await callUploadUrl({
        file_name: file.name,
        file_size: file.size,
        content_type: file.type,
      });

      const newTranscription = {
        id: newJobId,
        filename: file.name,
        status: "processing" as const,
        progress: 0,
        uploadedAt: new Date().toISOString().split("T")[0],
        duration: "Processing...", // Placeholder until we get actual duration
        size: `${(file.size / (1024 * 1024)).toFixed(2)} MB`,
      };

      const isLocalMode =
        uploadUrl.startsWith("/") || uploadUrl.includes("local-file.bin");

      if (isLocalMode) {
        await uploadFileLocally(uploadUrl, fileKey, file);
        console.log("Local file upload successful");
      } else {
        await uploadToS3(uploadUrl, file);
        console.log("S3 file upload successful");
      }

      // 3) Tell backend "file is in S3; enqueue job"
      await callCreateJob({
        jobId: newJobId,
        fileKey: fileKey,
        model: selectedModel,
        level: selectedLevel,
      });
      console.log("Job enqueued successfully");

      onFileUploaded(newTranscription);
    } catch (err) {
      console.error("Upload/Enqueue failed:", err);
      toast.error("Upload failed: " + (err as Error).message);
    }
  };

  const uploadFileLocally = async (
    uploadUrl: string,
    fileKey: string,
    file: File
  ) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("uploadUrl", uploadUrl);
    formData.append("fileKey", fileKey);

    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
    const response = await fetch(`${backendUrl}/uploadLocal`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    const result = await response.json();
    console.log("Local upload successful:", result);
    return result;
  };

  const handleFileInput = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.onchange = (e) => {
      const target = e.target as HTMLInputElement;
      if (target.files) {
        handleFiles(target.files);
      }
    };
    input.click();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload Audio File</CardTitle>
        <CardDescription>
          {metrics?.transcriptions_left !== undefined &&
          metrics.transcriptions_left !== null &&
          metrics.transcriptions_left <= 2 ? (
            <span className="text-yellow-600 font-medium">
              You have only {metrics.transcriptions_left} transcription
              {metrics.transcriptions_left === 1 ? "" : "s"} left this month.
            </span>
          ) : metrics?.transcriptions_left === 0 ? (
            <span className="text-red-600 font-medium">
              You have reached your monthly limit. Please upgrade to continue.
            </span>
          ) : (
            "Upload your audio file to convert it to piano sheet music"
          )}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-6 grid gap-6 md:grid-cols-2">
          <div>
            <h4 className="text-sm font-semibold mb-2">Model</h4>
            <RadioGroup
              value={selectedModel}
              onValueChange={(v) => setSelectedModel(v as any)}
              className="flex gap-4"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="amt" id="model-amt" />
                <Label htmlFor="model-amt">AMT (Better Musicality)</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="picogen" id="model-picogen" />
                <Label htmlFor="model-picogen">
                  PiCoGen (Better Timing and Accuracy)
                </Label>
              </div>
            </RadioGroup>
          </div>
          <div>
            <h4 className="text-sm font-semibold mb-2">Difficulty / Level</h4>
            <RadioGroup
              value={selectedLevel.toString()}
              onValueChange={(v) => {
                if (levelsDisabled) return;
                setSelectedLevel(Number(v) as 1 | 2 | 3);
              }}
              className={`flex gap-4 flex-wrap ${
                levelsDisabled ? "opacity-50 pointer-events-none" : ""
              }`}
              aria-disabled={levelsDisabled}
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem
                  value="1"
                  id="level-easy"
                  disabled={levelsDisabled}
                />
                <Label htmlFor="level-easy">Easy</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem
                  value="2"
                  id="level-medium"
                  disabled={levelsDisabled}
                />
                <Label htmlFor="level-medium">Medium</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem
                  value="3"
                  id="level-hard"
                  disabled={levelsDisabled}
                />
                <Label htmlFor="level-hard">Hard</Label>
              </div>
            </RadioGroup>
            <p className="text-xs text-muted-foreground mt-1">
              {levelsDisabled
                ? "Difficulty levels apply only to AMT."
                : "Select a difficulty for AMT transcription."}
            </p>
          </div>
        </div>
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive
              ? "border-primary bg-primary/5"
              : "border-muted-foreground/25"
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">
            Drop your audio file here
          </h3>
          <p className="text-muted-foreground mb-4">or click to browse files</p>
          <Button
            onClick={() => {
              handleFileInput();
            }}
          >
            Choose File
          </Button>
          <p className="text-xs text-muted-foreground mt-4">
            Supports MP3, WAV, FLAC up to 10MB
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default FileUploader;
