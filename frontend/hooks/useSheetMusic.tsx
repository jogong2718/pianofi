import { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";

interface UseSheetMusicProps {
    jobId: string;
}

interface SheetMusicData {
    xml: string;
    loading: boolean;
    error: string | null;
}

export function useSheetMusic({ jobId }: UseSheetMusicProps) {
    const [data, setData] = useState<SheetMusicData>({
        xml: "",
        loading: true,
        error: null,
    });

    const supabase = createClient();

    useEffect(() => {
        if (!jobId) return;

        const fetchXML = async () => {
            try {
                setData(prev => ({ ...prev, loading: true, error: null }));

                const {
                    data: { session },
                } = await supabase.auth.getSession();

                if (!session?.access_token) {
                    throw new Error("No authentication token found");
                }

                const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
                const response = await fetch(`${backendUrl}/getXML/${jobId}`, {
                    headers: {
                        'Accept': 'application/xml',
                        'Authorization': `Bearer ${session.access_token}`,
                    },
                });

                if (!response.ok) {
                    throw new Error(`Failed to fetch XML: ${response.statusText}`);
                }

                const xmlText = await response.text();
                setData({ xml: xmlText, loading: false, error: null });
            } catch (error) {
                setData({
                    xml: "",
                    loading: false,
                    error: error instanceof Error ? error.message : "Failed to fetch sheet music",
                });
            }
        };

        fetchXML();
    }, [jobId, supabase]);

    return data;
}