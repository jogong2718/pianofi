import { useState } from "react";

interface Transcription {
  id: string;
  filename: string;
  status: "processing" | "completed" | "failed";
  progress: number;
  uploadedAt: string;
  duration: string;
  size: string;
}

export const useFileUpload = () => {
  const [uploading, setUploading] = useState(false);

  const validateFile = (file: File): string | null => {
    const allowedTypes = ["audio/mp3", "audio/wav", "audio/flac", "audio/mpeg"];
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!allowedTypes.includes(file.type)) {
      return "Please upload an MP3, WAV, or FLAC file.";
    }

    if (file.size > maxSize) {
      return "File size must be less than 10MB.";
    }

    return null;
  };

  const uploadFile = async (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append("file", file);

    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

    const response = await fetch(`${backendUrl}/uploadfile`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Upload failed");
    }

    return response.json();
  };

  const handleFileUpload = async (
    file: File,
    onProgress?: (transcription: Transcription) => void,
    onComplete?: (transcription: Transcription) => void,
    onError?: (error: Error, transcriptionId: string) => void
  ) => {
    // Validate file first
    const validationError = validateFile(file);
    if (validationError) {
      throw new Error(validationError);
    }

    setUploading(true);

    const newTranscription: Transcription = {
      id: Date.now().toString(),
      filename: file.name,
      status: "processing",
      progress: 0,
      uploadedAt: new Date().toISOString().split("T")[0],
      duration: "0:00",
      size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
    };

    try {
      // Call onProgress to add transcription to UI immediately
      onProgress?.(newTranscription);

      // Upload file
      const result = await uploadFile(file);
      console.log("Upload successful:", result);

      // Mark as completed
      const completedTranscription = {
        ...newTranscription,
        progress: 100,
        status: "completed" as const,
      };

      onComplete?.(completedTranscription);
      return result;
    } catch (error) {
      console.error("Upload error:", error);
      onError?.(error as Error, newTranscription.id);
      throw error;
    } finally {
      setUploading(false);
    }
  };

  return {
    handleFileUpload,
    uploading,
    validateFile,
  };
};
