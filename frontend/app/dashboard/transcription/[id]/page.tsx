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
        <div className="container mx-auto px-4 py-8">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
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

            {/* Music Editor Placeholder */}
            <Card className="mb-6">
                <CardHeader>
                    <CardTitle>Music Editor</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="h-96 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center">
                        <div className="w-full h-full text-center text-gray-500">
                            {xml && (
                                <ViewSheetMusic musicXmlString={xml} />
                            )}
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Additional Info Card */}
            <Card>
                <CardHeader>
                    <CardTitle>Transcription Information</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <p className="text-sm text-gray-600">Job ID</p>
                            <p className="font-medium">{jobId}</p>
                        </div>
                        <div>
                            <p className="text-sm text-gray-600">Status</p>
                            <p className="font-medium text-green-600">Completed</p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}