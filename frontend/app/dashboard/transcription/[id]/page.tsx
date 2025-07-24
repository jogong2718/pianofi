"use client";

import { useParams } from "next/navigation";
import { useSheetMusic } from "@/hooks/useSheetMusic";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Download, Edit } from "lucide-react";
import { useRouter } from "next/navigation";
import ViewSheetMusic from "@/components/ViewSheetMusic";

export default function TranscriptionDetailPage() {
    const params = useParams();
    const router = useRouter();
    const jobId = params.id as string;

    const { xml, loading, error } = useSheetMusic({ jobId });

    if (loading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="animate-pulse space-y-4">
                    <div className="h-8 bg-gray-200 rounded w-1/4"></div>
                    <div className="h-96 bg-gray-200 rounded"></div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="text-center text-red-600">
                    <p>Error loading transcription: {error}</p>
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
                    <CardContent className="p-0 h-full">
                        <div className="h-full max-w-6xl mx-auto bg-gray-50 border-2 border-dashed border-gray-300 overflow-auto">
                            {xml && (
                                <ViewSheetMusic musicXmlString={xml} />
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}