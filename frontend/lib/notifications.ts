export class NotificationManager {
  static async requestPermission(): Promise<boolean> {
    if (!("Notification" in window)) return false;
    if (Notification.permission === "granted") return true;
    if (Notification.permission === "denied") return false;
    
    const permission = await Notification.requestPermission();
    return permission === "granted";
  }

  static showTranscriptionComplete(filename: string) {
    if (Notification.permission === "granted") {
      return new Notification("Transcription Complete", {
        body: `${filename} has been successfully transcribed`,
        icon: "/favicon.ico",
        tag: "transcription-complete",
        requireInteraction: true,
      });
    }
  }

  static showTranscriptionFailed(filename: string) {
    if (Notification.permission === "granted") {
      return new Notification("Transcription Failed", {
        body: `Failed to transcribe ${filename}`,
        icon: "/favicon.ico",
        tag: "transcription-failed",
      });
    }
  }
}