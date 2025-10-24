"use client";

import { useParams } from "next/navigation";
import { useMIDI, useSheetMusic, usePDF } from "@/hooks/useSheetMusic";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ArrowLeft, Download, Edit, AlertCircle, FileText } from "lucide-react";
import { useRouter } from "next/navigation";
import ViewSheetMusic from "@/components/ViewSheetMusic";
import { useAudio } from "@/hooks/useAudio";
import AudioPlayer from "@/components/audioPlayer";
import { toast } from "sonner";
import { useEffect } from "react";
import { useDownload } from "@/hooks/useDownload";

export default function TranscriptionDetailPage() {
    const params = useParams();
    const router = useRouter();
    const jobId = params.id as string;

    const { xml, loading: xmlLoading, error: xmlError } = useSheetMusic({ jobId });
    const { midi, loading: midiLoading, error: midiError } = useMIDI({ jobId });
    const { pdf, loading: pdfLoading, error: pdfError } = usePDF({ jobId });
    const { audioRef, metadata, loading: audioLoading, error: audioError } = useAudio({ jobId });
    
    // Use the download hook
    const { downloadMIDI, downloadXML, downloadPDF, downloading } = useDownload();

    // Simple wrapper functions
    const handleDownloadMIDI = () => downloadMIDI(midi, jobId);
    const handleDownloadXML = () => downloadXML(xml, jobId);
    const handleDownloadPDF = () => downloadPDF(pdf, jobId);

    // Show toast notifications for non-critical errors
    useEffect(() => {
        if (!midiLoading && midiError) {
            toast.error("MIDI Download Unavailable", {
                description: midiError,
                duration: 5000,
            });
        }
    }, [midiError, midiLoading]);

    useEffect(() => {
        if (!audioLoading && audioError) {
            toast.error("Audio Playback Unavailable", {
                description: audioError,
                duration: 5000,
            });
        }
    }, [audioError, audioLoading]);

    useEffect(() => {
        if (!pdfLoading && pdfError) {
            toast.error("PDF Download Unavailable", {
            description: pdfError,
            duration: 5000,
            });
        }
    }, [pdfError, pdfLoading]);

    if (xmlLoading || audioLoading) {
        return (
            <div className="h-screen flex flex-col bg-gradient-to-br from-purple-50 to-blue-50 dark:bg-none dark:from-transparent dark:to-transparent dark:bg-background">
                <div className="container mx-auto md:px-4 pt-8 flex flex-col h-full">
                    {/* Header with 3 button skeletons */}
                    <div className="flex items-center justify-between mb-6 flex-shrink-0">
                        <div className="flex items-center space-x-4">
                            <div className="animate-pulse h-9 w-32 bg-gray-300 dark:bg-gray-600 rounded"></div> {/* Back button */}
                            <h1 className="text-2xl font-bold"></h1>
                        </div>

                        <div className="flex items-center space-x-2">
                            <div className="animate-pulse h-9 w-16 lg:w-32 bg-gray-300 dark:bg-gray-600 rounded"></div> {/* Download XML button */}
                            <div className="animate-pulse h-9 w-16 lg:w-32 bg-gray-300 dark:bg-gray-600 rounded"></div> {/* Download MIDI button */}
                            <div className="animate-pulse h-9 w-20 lg:w-36 bg-gray-300 dark:bg-gray-600 rounded"></div> {/* Edit Sheet Music button */}
                        </div>
                    </div>

                    {/* Music Editor */}
                    <Card className="flex-1 min-h-0">
                        <CardContent className="p-0 h-full flex flex-col">
                            <div className="h-full flex-1 w-full mx-auto bg-gray-50 dark:bg-gray-900 overflow-x-hidden overflow-y-auto min-h-0">
                                <div className="w-full min-h-full bg-background flex flex-col">
                                    {/* Audio Player skeleton */}
                                    <div className="w-full bg-background border-b border-border p-3 flex-shrink-0">
                                        <div className="animate-pulse h-16 w-full bg-gray-300 dark:bg-gray-600 rounded"></div> {/* Audio player */}
                                    </div>
                                    
                                    {/* Sheet Music Editor skeleton */}
                                    <div className="w-full flex-1 bg-background min-h-0">
                                        <div className="w-full relative max-w-6xl mx-auto rounded-lg p-3" style={{ height: 'calc(100vh - 200px)' }}>
                                            <div className="animate-pulse h-full w-full bg-gray-300 dark:bg-gray-600 rounded"></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        );
    }

    // Only show critical error that prevents the core functionality (XML required for OSMD)
    if (xmlError) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 dark:bg-none dark:from-transparent dark:to-transparent dark:bg-background">
                <div className="container mx-auto px-4 py-8">
                    <div className="max-w-2xl mx-auto space-y-4">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => router.push("/dashboard")}
                            className="mb-4"
                        >
                            <ArrowLeft className="h-4 w-4 mr-2" />
                            Back to Dashboard
                        </Button>
                        
                        <Alert variant="destructive">
                            <AlertCircle className="h-4 w-4" />
                            <AlertTitle>Cannot Load Sheet Music</AlertTitle>
                            <AlertDescription>
                                {xmlError}
                            </AlertDescription>
                        </Alert>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="h-screen flex flex-col bg-gradient-to-br from-purple-50 to-blue-50 dark:bg-none dark:from-transparent dark:to-transparent dark:bg-background">
            <div className="container mx-auto md:px-4 pt-8 flex flex-col h-full">
                {/* Header - Responsive */}
                <div className="flex items-center justify-between mb-6 flex-shrink-0 gap-4">
                    {/* Left side - Back button + Title */}
                    <div className="flex items-center space-x-4 min-w-0 flex-1">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => router.push("/dashboard")}
                            className="hover:cursor-pointer flex-shrink-0"
                        >
                            <ArrowLeft className="h-4 w-4 mr-2" />
                            <span className="hidden sm:inline">Back to Dashboard</span>
                            <span className="sm:hidden">Back</span>
                        </Button>
                        {/* Hide title on mobile */}
                        <h1 className="text-2xl font-bold hidden md:block truncate">
                            Transcription Details
                        </h1>
                    </div>

                    {/* Right side - Download buttons */}
                    <div className="flex items-center space-x-2 flex-shrink-0">
                        {/* Desktop: All buttons with text */}
                        <div className="hidden lg:flex items-center space-x-2">
                            <Button 
                                variant="outline" 
                                size="sm"
                                onClick={handleDownloadXML}
                                disabled={!xml || xmlLoading || downloading === `transcription-${jobId}.xml`}
                                className="hover:cursor-pointer"
                            >
                                <Download className="h-4 w-4 mr-2" />
                                {downloading === `transcription-${jobId}.xml` ? "Downloading..." : "Download XML"}
                            </Button>
                            <Button 
                                variant="outline" 
                                size="sm"
                                onClick={handleDownloadMIDI}
                                disabled={!midi || midiLoading || downloading === `transcription-${jobId}.mid`}
                                className="hover:cursor-pointer"
                            >
                                <Download className="h-4 w-4 mr-2" />
                                {downloading === `transcription-${jobId}.mid` ? "Downloading..." : "Download MIDI"}
                            </Button>
                            <Button 
                                variant="outline" 
                                size="sm"
                                onClick={handleDownloadPDF}
                                disabled={!pdf || pdfLoading || downloading === `transcription-${jobId}.pdf`}
                                className="hover:cursor-pointer"
                            >
                                <FileText className="h-4 w-4 mr-2" />
                                {downloading === `transcription-${jobId}.pdf` ? "Downloading..." : "Download PDF"}
                            </Button>
                        </div>

                        {/* Tablet: Shorter text */}
                        <div className="hidden md:flex lg:hidden items-center space-x-2">
                            <Button 
                                variant="outline" 
                                size="sm"
                                onClick={handleDownloadXML}
                                disabled={!xml || xmlLoading || downloading === `transcription-${jobId}.xml`}
                                className="hover:cursor-pointer"
                            >
                                <Download className="h-4 w-4 mr-1" />
                                XML
                            </Button>
                            <Button 
                                variant="outline" 
                                size="sm"
                                onClick={handleDownloadMIDI}
                                disabled={!midi || midiLoading || downloading === `transcription-${jobId}.mid`}
                                className="hover:cursor-pointer"
                            >
                                <Download className="h-4 w-4 mr-1" />
                                MIDI
                            </Button>
                            <Button 
                                variant="outline" 
                                size="sm"
                                onClick={handleDownloadPDF}
                                disabled={!pdf || pdfLoading || downloading === `transcription-${jobId}.pdf`}
                                className="hover:cursor-pointer"
                            >
                                <FileText className="h-4 w-4 mr-1" />
                                PDF
                            </Button>
                        </div>

                        {/* Mobile: Compact buttons with text */}
                        <div className="flex md:hidden items-center space-x-1">
                            <Button 
                                variant="outline" 
                                size="sm"
                                onClick={handleDownloadXML}
                                disabled={!xml || xmlLoading || downloading === `transcription-${jobId}.xml`}
                                className="hover:cursor-pointer px-2"
                                title="Download XML"
                            >
                                <Download className="h-4 w-4 mr-1" />
                                XML
                            </Button>
                            <Button 
                                variant="outline" 
                                size="sm"
                                onClick={handleDownloadMIDI}
                                disabled={!midi || midiLoading || downloading === `transcription-${jobId}.mid`}
                                className="hover:cursor-pointer px-2"
                                title="Download MIDI"
                            >
                                <Download className="h-4 w-4 mr-1" />
                                MIDI
                            </Button>
                            <Button 
                                variant="outline" 
                                size="sm"
                                onClick={handleDownloadPDF}
                                disabled={!pdf || pdfLoading || downloading === `transcription-${jobId}.pdf`}
                                className="hover:cursor-pointer px-2"
                                title="Download PDF"
                            >
                                <FileText className="h-4 w-4 mr-1" />
                                PDF
                            </Button>
                        </div>
                    </div>
                </div>

                {/* Music Editor - Grows to fill remaining space */}
                <Card className="flex-1 min-h-0">
                    <CardContent className="p-0 h-full flex flex-col">
                        <div className="h-full flex-1 w-full mx-auto bg-gray-50 dark:bg-gray-900 overflow-x-hidden overflow-y-auto min-h-0">
                            {xml && (
                                <ViewSheetMusic jobId={jobId} musicXmlString={xml} audioRef={audioRef} metadata={metadata} />
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}