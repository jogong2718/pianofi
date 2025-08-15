import { useState } from 'react';
import { toast } from 'sonner';

type DataType = 'text' | 'arrayBuffer' | 'midi';

interface UseDownloadOptions {
  showToasts?: boolean;
}

export function useDownload(options: UseDownloadOptions = {}) {
  const { showToasts = true } = options;
  const [downloading, setDownloading] = useState<string | null>(null);

  const downloadFile = async (
    data: any, 
    filename: string, 
    mimeType: string, 
    dataType: DataType
  ) => {
    if (!data) {
      if (showToasts) {
        toast.error(`${filename.split('.').pop()?.toUpperCase()} data not available`);
      }
      return false;
    }

    setDownloading(filename);

    try {
      let blob: Blob;

      switch (dataType) {
        case 'text':
          blob = new Blob([data], { type: mimeType });
          break;
        case 'arrayBuffer':
          blob = new Blob([data], { type: mimeType });
          break;
        case 'midi':
          const midiArrayBuffer = data.toArray();
          blob = new Blob([midiArrayBuffer], { type: mimeType });
          break;
        default:
          throw new Error('Unsupported data type');
      }

      // Create download URL and trigger download
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      if (showToasts) {
        toast.success(`${filename.split('.').pop()?.toUpperCase()} file downloaded successfully!`);
      }
      return true;
    } catch (error) {
      console.error(`Error downloading ${filename}:`, error);
      if (showToasts) {
        toast.error(`Failed to download ${filename.split('.').pop()?.toUpperCase()} file`);
      }
      return false;
    } finally {
      setDownloading(null);
    }
  };

  // Convenience methods for specific file types
  const downloadMIDI = (midi: any, jobId: string) => 
    downloadFile(midi, `transcription-${jobId}.mid`, 'audio/midi', 'midi');

  const downloadXML = (xml: string, jobId: string) => 
    downloadFile(xml, `transcription-${jobId}.xml`, 'application/xml', 'text');

  const downloadPDF = async (data: ArrayBuffer, jobId: string) => 
    downloadFile(data, `transcription-${jobId}.pdf`, 'application/pdf', 'arrayBuffer');

  return {
    downloadFile,
    downloadMIDI,
    downloadXML,
    downloadPDF,
    downloading,
    isDownloading: downloading !== null,
  };
}