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
import { useProcessYoutubeUrl } from "@/hooks/useProcessYoutubeUrl";
import { uploadToS3 } from "@/lib/utils";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

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
  const [youtubeUrl, setYoutubeUrl] = useState("");

  const { callUploadUrl, loading: loadingUploadUrl } = useUploadUrl();

  const { callCreateJob, loading: loadingCreateJob } = useCreateJob();

  const { callProcessYoutubeUrl, loading: loadingYoutube } = useProcessYoutubeUrl();

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

    // Check if PiCoGen is selected and show error
    if (selectedModel === "picogen") {
      toast.error(
        "PiCoGen model is currently unavailable. Please select AMT model."
      );
      return;
    }
    // remove when picogen is available

    if (metricsLoading) {
      toast.error("Please wait while we check your subscription limits...");
      return;
    }

    if (
      metrics?.transcriptions_left !== undefined &&
      metrics.transcriptions_left !== null &&
      metrics.transcriptions_left <= 0
    ) {
      toast.error("You have reached your monthly transcription limit.");
      // onUpgradeRequired(); uncomment when payment flow is ready
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

  const handleYoutubeSubmit = async () => {
    console.log("handleYoutubeSubmit called");
    if (!user) return;

    // Check if PiCoGen is selected
    if (selectedModel === "picogen") {
      toast.error(
        "PiCoGen model is currently unavailable. Please select AMT model."
      );
      return;
    }

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

    if (!youtubeUrl.trim()) {
      toast.error("Please enter a YouTube URL");
      return;
    }

    // Validate YouTube URL format
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
    if (!youtubeRegex.test(youtubeUrl)) {
      toast.error("Invalid YouTube URL format");
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

    try {
      toast.info("Processing YouTube video...");

      const { jobId, fileKey } = await callProcessYoutubeUrl({
        youtube_url: youtubeUrl,
        model: selectedModel,
        level: selectedLevel,
      });

      const newTranscription = {
        id: jobId,
        filename: "YouTube Video",
        status: "processing" as const,
        progress: 0,
        uploadedAt: new Date().toISOString().split("T")[0],
        duration: "Processing...",
        size: "N/A",
      };

      onFileUploaded(newTranscription);
      setYoutubeUrl(""); // Clear input
      toast.success("YouTube video queued for processing!");
    } catch (err) {
      console.error("YouTube processing failed:", err);
      toast.error("Failed to process YouTube URL: " + (err as Error).message);
    }
  };

  // helper styling builders
  const modelOptionClass = (v: "amt" | "picogen") =>
    `cursor-pointer rounded-md border px-4 py-3 text-sm transition-all flex items-start gap-2 w-full
     ${
       selectedModel === v
         ? "bg-primary/10 border-primary ring-2 ring-primary/40"
         : "border-muted-foreground/20 hover:border-primary/50 hover:bg-primary/5"
     }`;

  const levelOptionClass = (v: 1 | 2 | 3) =>
    `cursor-pointer rounded-md border px-4 py-4 text-xs sm:text-sm font-medium transition-all flex items-center gap-2
     ${
       selectedLevel === v
         ? "bg-primary/10 border-primary ring-2 ring-primary/40"
         : "border-muted-foreground/20 hover:border-primary/40 hover:bg-primary/5"
     } ${levelsDisabled ? "opacity-50" : ""}`;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload Audio or YouTube URL</CardTitle>
        <CardDescription>
          {selectedModel === "picogen" ? (
            <span className="text-orange-600 font-medium">
              PiCoGen model is currently unavailable. Please select AMT to
              continue.
            </span>
          ) : metrics?.transcriptions_left !== undefined &&
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
        {/* <CardDescription>
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
        </CardDescription> */}
      </CardHeader>
      <CardContent>
        {/* Reworked selection layout */}
        <div className="mb-10 flex flex-col md:flex-row justify-center items-start gap-8">
          <div className="flex-1 max-w-md mx-auto md:mx-0">
            <div className="rounded-xl border border-border/60 bg-muted/10 backdrop-blur-sm p-4 md:p-5 h-full">
              <h4 className="text-sm font-semibold mb-3 tracking-wide uppercase text-muted-foreground">
                Model
              </h4>
              <RadioGroup
                value={selectedModel}
                onValueChange={(v) => setSelectedModel(v as any)}
                className="space-y-3"
              >
                <Label
                  htmlFor="model-amt"
                  className={modelOptionClass("amt")}
                  onClick={() => setSelectedModel("amt")}
                >
                  <RadioGroupItem
                    value="amt"
                    id="model-amt"
                    className="mt-0.5"
                  />
                  <div>
                    <div className="font-medium">AMT</div>
                    <p className="text-xs text-muted-foreground">
                      Better musicality & faster turnaround
                    </p>
                  </div>
                </Label>

                <Label
                  htmlFor="model-picogen"
                  className={`${modelOptionClass(
                    "picogen"
                  )} opacity-60 cursor-not-allowed`}
                  onClick={() => {
                    setSelectedModel("picogen");
                    toast.warning("PiCoGen model is currently unavailable");
                  }}
                >
                  <RadioGroupItem
                    value="picogen"
                    id="model-picogen"
                    className="mt-0.5"
                  />
                  <div>
                    <div className="font-medium flex items-center gap-2">
                      PiCoGen
                      <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full">
                        Unavailable
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Higher timing precision & note accuracy
                    </p>
                  </div>
                </Label>
                {/* <Label
                  htmlFor="model-picogen"
                  className={modelOptionClass("picogen")}
                  onClick={() => setSelectedModel("picogen")}
                >
                  <RadioGroupItem
                    value="picogen"
                    id="model-picogen"
                    className="mt-0.5"
                  />
                  <div>
                    <div className="font-medium">PiCoGen</div>
                    <p className="text-xs text-muted-foreground">
                      Higher timing precision & note accuracy
                    </p>
                  </div>
                </Label> */}
              </RadioGroup>
            </div>
          </div>

          {/* Difficulty */}
          <div className="flex-1 max-w-md mx-auto md:mx-0">
            <div
              className={`rounded-xl border border-border/60 bg-muted/10 backdrop-blur-sm p-5 md:p-6 h-full transition-opacity ${
                levelsDisabled ? "opacity-60" : ""
              }`}
            >
              <h4 className="text-sm font-semibold mb-5 tracking-wide uppercase text-muted-foreground">
                Difficulty / Level
              </h4>
              <RadioGroup
                value={selectedLevel.toString()}
                onValueChange={(v) => {
                  if (levelsDisabled) return;
                  setSelectedLevel(Number(v) as 1 | 2 | 3);
                }}
                className="grid grid-cols-3 gap-4"
                aria-disabled={levelsDisabled}
              >
                <Label
                  htmlFor="level-easy"
                  className={levelOptionClass(1)}
                  onClick={() => !levelsDisabled && setSelectedLevel(1)}
                >
                  <RadioGroupItem
                    value="1"
                    id="level-easy"
                    disabled={levelsDisabled}
                    className="hidden"
                  />
                  Easy
                </Label>
                <Label
                  htmlFor="level-medium"
                  className={levelOptionClass(2)}
                  onClick={() => !levelsDisabled && setSelectedLevel(2)}
                >
                  <RadioGroupItem
                    value="2"
                    id="level-medium"
                    disabled={levelsDisabled}
                    className="hidden"
                  />
                  Medium
                </Label>
                <Label
                  htmlFor="level-hard"
                  className={levelOptionClass(3)}
                  onClick={() => !levelsDisabled && setSelectedLevel(3)}
                >
                  <RadioGroupItem
                    value="3"
                    id="level-hard"
                    disabled={levelsDisabled}
                    className="hidden"
                  />
                  Hard
                </Label>
              </RadioGroup>
              <p className="text-xs text-muted-foreground mt-5">
                {levelsDisabled
                  ? "Difficulty levels apply only to AMT."
                  : "Choose how simplified or complex you want the transcription."}
              </p>
            </div>
          </div>
        </div>

        <Tabs defaultValue="file" className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-4">
            <TabsTrigger value="file">Upload File</TabsTrigger>
            <TabsTrigger value="youtube">YouTube URL</TabsTrigger>
          </TabsList>

          <TabsContent value="file">
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                selectedModel === "picogen"
                  ? "border-muted-foreground/25 opacity-50 cursor-not-allowed"
                  : dragActive
                  ? "border-primary bg-primary/5"
                  : "border-muted-foreground/25"
              }`}
              onDragEnter={selectedModel !== "picogen" ? handleDrag : undefined}
              onDragLeave={selectedModel !== "picogen" ? handleDrag : undefined}
              onDragOver={selectedModel !== "picogen" ? handleDrag : undefined}
              onDrop={selectedModel !== "picogen" ? handleDrop : undefined}
            >
              <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">
                Drop your audio file here
              </h3>
              <p className="text-muted-foreground mb-4">or click to browse files</p>
              <Button
                onClick={() => {
                  if (selectedModel === "picogen") {
                    toast.error(
                      "PiCoGen model is currently unavailable. Please select AMT model."
                    );
                    return;
                  }
                  handleFileInput();
                }}
                disabled={selectedModel === "picogen"}
              >
                Choose File
              </Button>
              <p className="text-xs text-muted-foreground mt-4">
                Supports MP3, WAV, FLAC up to 10MB
              </p>
            </div>
          </TabsContent>

          <TabsContent value="youtube">
            <div className="border-2 border-dashed rounded-lg p-8 text-center">
              <div className="max-w-md mx-auto">
                <h3 className="text-lg font-semibold mb-2">
                  Process YouTube Video
                </h3>
                <p className="text-muted-foreground mb-4">
                  Enter a YouTube URL to extract and process the audio
                </p>
                <div className="flex gap-2">
                  <Input
                    type="url"
                    placeholder="https://www.youtube.com/watch?v=..."
                    value={youtubeUrl}
                    onChange={(e) => setYoutubeUrl(e.target.value)}
                    disabled={selectedModel === "picogen" || loadingYoutube}
                    className="flex-1"
                  />
                  <Button
                    onClick={handleYoutubeSubmit}
                    disabled={selectedModel === "picogen" || loadingYoutube || !youtubeUrl.trim()}
                  >
                    {loadingYoutube ? "Processing..." : "Process"}
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground mt-4">
                  Supports YouTube and YouTube Music URLs
                </p>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default FileUploader;
