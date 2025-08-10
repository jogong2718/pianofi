"use client";

import { useParams } from "next/navigation";
import { useMIDI, useSheetMusic } from "@/hooks/useSheetMusic";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ArrowLeft, Download, Edit, AlertCircle } from "lucide-react";
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
            <div className="container mx-auto px-4 py-8">
                <div className="animate-pulse space-y-4">
                    <div className="h-8 bg-gray-200 rounded w-1/4"></div>
                    <div className="h-96 bg-gray-200 rounded"></div>
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
                            <Edit className="h-4 w-4 mr-2" />
                            Edit Sheet Music
                        </Button>
                    </div>
                </div>

                {/* Music Editor - Grows to fill remaining space */}
                <Card className="flex-1 min-h-0">
                    <CardContent className="p-0 h-full flex flex-col">
                        <AudioPlayer jobId={jobId} audioRef={audioRef} metadata={metadata} />
                        <div className="h-full flex-1 max-w-6xl w-full mx-auto bg-gray-50 overflow-x-hidden overflow-y-auto">
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