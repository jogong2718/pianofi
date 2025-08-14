"use client";

import { useParams } from "next/navigation";
import { useMIDI, useSheetMusic } from "@/hooks/useSheetMusic";
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

export default function TranscriptionDetailPage() {
    const params = useParams();
    const router = useRouter();
    const jobId = params.id as string;

    const { xml, loading: xmlLoading, error: xmlError } = useSheetMusic({ jobId });
    const { midi, loading: midiLoading, error: midiError } = useMIDI({ jobId });
    const { audioRef, metadata, loading: audioLoading, error: audioError } = useAudio({ jobId });

    // Show toast notifications for non-critical errors
    useEffect(() => {
        if (midiError) {
            toast.error("MIDI Download Unavailable", {
                description: midiError,
                duration: 5000,
            });
        }
    }, [midiError]);

    useEffect(() => {
        if (audioError) {
            toast.error("Audio Playback Unavailable", {
                description: audioError,
                duration: 5000,
            });
        }
    }, [audioError]);

    if (xmlLoading || audioLoading) {
        return (
            <div className="h-screen flex flex-col">
                <div className="container mx-auto md:px-4 pt-8 flex flex-col h-full">
                    {/* Header with 3 button skeletons */}
                    <div className="flex items-center justify-between mb-6 flex-shrink-0">
                        <div className="flex items-center space-x-4">
                            <div className="animate-pulse h-9 w-32 bg-gray-700 rounded"></div> {/* Back button */}
                            <h1 className="text-2xl font-bold"></h1>
                        </div>

                        <div className="flex items-center space-x-2">
                            <div className="animate-pulse h-9 w-32 bg-gray-700 rounded"></div> {/* Download MIDI button */}
                            <div className="animate-pulse h-9 w-36 bg-gray-700 rounded"></div> {/* Edit Sheet Music button */}
                        </div>
                    </div>

                    {/* Music Editor */}
                    <Card className="flex-1 min-h-0">
                        <CardContent className="p-0 h-full flex flex-col">
                            <div className="h-full flex-1 w-full mx-auto bg-gray-50 overflow-x-hidden overflow-y-auto min-h-0">
                                <div className="w-full min-h-full bg-gray-900 dark:bg-black flex flex-col">
                                    {/* Audio Player skeleton */}
                                    <div className="w-full bg-gray-900 dark:bg-black border-b border-gray-700 dark:border-gray-800 p-3 flex-shrink-0">
                                        <div className="animate-pulse h-16 w-full bg-gray-700 rounded"></div> {/* Audio player */}
                                    </div>
                                    
                                    {/* Sheet Music Editor skeleton */}
                                    <div className="w-full flex-1 bg-gray-900 dark:bg-black min-h-0">
                                        <div className="w-full relative max-w-6xl mx-auto rounded-lg p-3" style={{ height: 'calc(100vh - 200px)' }}>
                                            <div className="animate-pulse h-full w-full bg-gray-700 rounded"></div>
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
        );
    }

    return (
        <div className="h-screen flex flex-col">
            <div className="container mx-auto md:px-4 pt-8 flex flex-col h-full">
                {/* Header - Fixed size */}
                <div className="flex items-center justify-between mb-6 flex-shrink-0">
                    <div className="flex items-center space-x-4">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => router.push("/dashboard")}
                        >
                            <ArrowLeft className="h-4 w-4 mr-2" />
                            Back to Dashboard
                        </Button>
                        <h1 className="text-2xl font-bold">Transcription Details</h1>
                    </div>

                    <div className="flex items-center space-x-2">
                        <Button variant="outline" size="sm">
                            <Download className="h-4 w-4 mr-2" />
                            Download MIDI
                        </Button>
                        <Button variant="outline" size="sm">
                            <FileText className="h-4 w-4 mr-2" />
                            Download PDF
                        </Button>
                    </div>
                </div>

                {/* Music Editor - Grows to fill remaining space */}
                <Card className="flex-1 min-h-0">
                    <CardContent className="p-0 h-full flex flex-col">
                        <div className="h-full flex-1 w-full mx-auto bg-gray-50 overflow-x-hidden overflow-y-auto min-h-0">
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