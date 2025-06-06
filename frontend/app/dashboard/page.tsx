"use client";

import React, { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Upload,
  Music,
  FileText,
  Download,
  Clock,
  CheckCircle,
  AlertCircle,
  MoreHorizontal,
  User,
  Settings,
  LogOut,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ThemeToggle } from "@/components/theme-toggle";
import { createClient } from "@/lib/supabase/client";

import { useUploadUrl } from "@/hooks/useUploadUrl";
import { uploadToS3 } from "@/lib/utils";
import { useCreateJob } from "@/hooks/useCreateJob";

interface Transcription {
  id: string;
  filename: string;
  status: "processing" | "completed" | "failed";
  progress: number;
  uploadedAt: string;
  duration: string;
  size: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const supabase = createClient();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const getUser = async () => {
      const {
        data: { user },
        error,
      } = await supabase.auth.getUser();

      if (error || !user) {
        router.push("/login");
        return;
      }

      setUser(user);
      setLoading(false);
    };

    getUser();

    const confirmed = searchParams.get("confirmed");
    if (confirmed === "true") {
      toast.success("Email verified successfully!");
    }
  }, [searchParams, router, supabase.auth]);

  const handleLogout = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) {
      toast.error("Logout failed: " + error.message);
    } else {
      router.push("/");
    }
  };

  const [transcriptions, setTranscriptions] = useState<Transcription[]>([
    {
      id: "1",
      filename: "bohemian-rhapsody.mp3",
      status: "completed",
      progress: 100,
      uploadedAt: "2024-01-15",
      duration: "5:55",
      size: "8.2 MB",
    },
    {
      id: "2",
      filename: "moonlight-sonata.wav",
      status: "processing",
      progress: 65,
      uploadedAt: "2024-01-15",
      duration: "3:20",
      size: "12.1 MB",
    },
    {
      id: "3",
      filename: "imagine.mp3",
      status: "completed",
      progress: 100,
      uploadedAt: "2024-01-14",
      duration: "3:03",
      size: "4.8 MB",
    },
  ]);

  const [dragActive, setDragActive] = useState(false);

  const {
    callUploadUrl,
    loading: loadingUploadUrl,
    error: uploadUrlError,
  } = useUploadUrl();

  const {
    callCreateJob,
    loading: loadingCreateJob,
    error: CreateJobError,
  } = useCreateJob();

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
    // File existence
    if (!file) {
      return "No file selected";
    }

    // File type validation
    const allowedTypes = ["audio/mpeg", "audio/wav", "audio/flac"];
    if (!allowedTypes.includes(file.type)) {
      return "Unsupported file type. Please upload MP3, WAV, or FLAC.";
    }

    // File size validation (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB in bytes
    if (file.size > maxSize) {
      return "File too large. Maximum size is 10MB.";
    }

    // File name validation
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
        user_id: user.id,
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
        duration: "N/A",
        size: "", // Will be set below
      };

      const isLocalMode =
        uploadUrl.startsWith("/") || uploadUrl.includes("local-file.bin");

      if (isLocalMode) {
        await uploadFileLocally(file);
        newTranscription.size = "local_test MB";
        console.log("Local file upload successful");
      } else {
        await uploadToS3(uploadUrl, file);
        newTranscription.size = `${(file.size / (1024 * 1024)).toFixed(2)} MB`;
        console.log("S3 file upload successful");
      }

      setTranscriptions((prev) => [newTranscription, ...prev]);

      // 3) Tell backend “file is in S3; enqueue job”
      await callCreateJob({
        jobId: newJobId,
        fileKey: fileKey,
        userId: user.id,
      });
      console.log("Job enqueued successfully");

      // // 4) Now that the job is enqueued, store jobId so we can start polling
      // setJobId(newJobId);
    } catch (err) {
      console.error("Upload/Enqueue failed:", err);
      toast.error("Upload failed: " + (err as Error).message);
    }
  };

  const uploadFileLocally = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);

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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "processing":
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case "failed":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "completed":
        return "Completed";
      case "processing":
        return "Processing";
      case "failed":
        return "Failed";
      default:
        return "Unknown";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Music className="h-8 w-8 text-primary mx-auto mb-4" />
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="flex h-16 items-center px-4 lg:px-6">
          <div className="flex items-center space-x-4">
            <Music className="h-8 w-8 text-primary" />
            <span className="text-2xl font-bold">PianoFi</span>
          </div>

          <div className="ml-auto flex items-center space-x-4">
            <ThemeToggle />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="relative h-8 w-8 rounded-full"
                >
                  <Avatar className="h-8 w-8">
                    <AvatarImage
                      src="/middlegura.svg?height=32&width=32"
                      alt="User"
                    />
                    <AvatarFallback>
                      {user?.user_metadata?.first_name?.[0] ||
                        user?.email?.[0] ||
                        "U"}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="end" forceMount>
                <DropdownMenuLabel className="font-normal">
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium leading-none">
                      {user?.user_metadata?.first_name &&
                      user?.user_metadata?.last_name
                        ? `${user.user_metadata.first_name} ${user.user_metadata.last_name}`
                        : user?.email}
                    </p>
                    <p className="text-xs leading-none text-muted-foreground">
                      {user?.email}
                    </p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem>
                  <User className="mr-2 h-4 w-4" />
                  <span>Profile</span>
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Settings className="mr-2 h-4 w-4" />
                  <span>Settings</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Log out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      <div className="flex-1 space-y-4 p-4 lg:p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        </div>

        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Total Transcriptions
              </CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">24</div>
              <p className="text-xs text-muted-foreground">
                +3 from last month
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Processing</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">1</div>
              <p className="text-xs text-muted-foreground">
                Estimated 2 minutes remaining
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">This Month</CardTitle>
              <Music className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">8</div>
              <p className="text-xs text-muted-foreground">
                92 remaining in plan
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Success Rate
              </CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">98%</div>
              <p className="text-xs text-muted-foreground">
                +2% from last month
              </p>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="upload" className="space-y-4">
          <TabsList>
            <TabsTrigger value="upload">Upload</TabsTrigger>
            <TabsTrigger value="transcriptions">My Transcriptions</TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Upload Audio File</CardTitle>
                <CardDescription>
                  Upload your audio file to convert it to piano sheet music
                </CardDescription>
              </CardHeader>
              <CardContent>
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
                  <p className="text-muted-foreground mb-4">
                    or click to browse files
                  </p>
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
          </TabsContent>

          <TabsContent value="transcriptions" className="space-y-4">
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
                    <div
                      key={transcription.id}
                      className="flex flex-col space-y-4 sm:flex-row sm:space-y-0 items-center justify-between p-4 border rounded-lg"
                    >
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(transcription.status)}
                          <div>
                            <p className="font-medium">
                              {transcription.filename}
                            </p>
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
                            {getStatusText(transcription.status)}
                          </Badge>
                          {transcription.status === "processing" && (
                            <div className="w-24">
                              <Progress value={transcription.progress} />
                            </div>
                          )}
                        </div>

                        {transcription.status === "completed" && (
                          <Button size="sm" variant="outline">
                            <Download className="h-4 w-4 mr-2" />
                            Download
                          </Button>
                        )}

                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>View Details</DropdownMenuItem>
                            <DropdownMenuItem>Reprocess</DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="text-red-600">
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
