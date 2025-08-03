import { useState, useEffect, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import { OpenSheetMusicDisplay } from "opensheetmusicdisplay";
import { Midi } from '@tonejs/midi'

interface UseSheetMusicProps {
    jobId: string;
}

interface SheetMusicData {
    xml: string;
    loading: boolean;
    error: string | null;
}

interface UseOSMDProps {
    musicXml?: string;
}

interface UseMIDIProps {
    jobId: string;
}

interface MIDIData {
    midi: Midi | null;
    loading: boolean;
    error: string | null;
}

interface UseAudioProps {
    jobId: string;
}

interface AudioData {
    audioUrl: string | null;
    metadata: any | null;
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
                console.log('Getting XML for jobId:', jobId);
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

                console.log('XML fetched successfully');
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

export function useMIDI({ jobId }: UseMIDIProps) {
    const [data, setData] = useState<MIDIData>({
        midi: null,
        loading: true,
        error: null,
    });

    const supabase = createClient();

    

    useEffect(() => {
        if (!jobId) return;

        const fetchMIDI = async () => {
            try {
                console.log('Getting MIDI for jobId:', jobId);
                setData(prev => ({ ...prev, loading: true, error: null }));

                const {
                    data: { session },
                } = await supabase.auth.getSession();

                if (!session?.access_token) {
                    throw new Error("No authentication token found");
                }

                const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
                const response = await fetch(`${backendUrl}/getMIDI/${jobId}`, {
                    headers: {
                        'Accept': 'application/json',
                        'Authorization': `Bearer ${session.access_token}`,
                    },
                });

                if (!response.ok) {
                    throw new Error(`Failed to fetch MIDI: ${response.statusText}`);
                }

                const midiContent = await response.arrayBuffer();
                const midi = new Midi(midiContent);
                setData({ midi, loading: false, error: null });

                console.log('MIDI fetched successfully');
            } catch (error) {
                setData({ midi: null, loading: false, error: error instanceof Error ? error.message : "Failed to fetch MIDI" });
            }
        }

        fetchMIDI();
    }, [jobId, supabase]);

    return data;
}

export function useAudio({ jobId }: UseAudioProps) {
    const [data, setData] = useState<AudioData>({
        audioUrl: null,
        metadata: null,
        loading: true,
        error: null,
    });

    const supabase = createClient();

    useEffect(() => {
        if (!jobId) return;

        const fetchAudio = async () => {
            try {
                console.log('Getting Audio for jobId:', jobId);
                setData(prev => ({ ...prev, loading: true, error: null }));

                const {
                    data: { session },
                } = await supabase.auth.getSession();

                if (!session?.access_token) {
                    throw new Error("No authentication token found");
                }

                const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
                const response = await fetch(`${backendUrl}/getAudio/${jobId}`, {
                    headers: {
                        'Accept': 'audio/wav',
                        'Authorization': `Bearer ${session.access_token}`,
                    },
                });

                if (!response.ok) {
                    throw new Error(`Failed to fetch Audio: ${response.statusText}`);
                }

                // Get audio content as blob
                const audioBlob = await response.blob();
                const audioUrl = URL.createObjectURL(audioBlob);

                // Get metadata from headers
                const metadataHeader = response.headers.get('X-Audio-Metadata');
                const metadata = metadataHeader ? JSON.parse(metadataHeader) : null;

                setData({ 
                    audioUrl, 
                    metadata, 
                    loading: false, 
                    error: null 
                });

                console.log('Audio fetched successfully', { metadata });
            } catch (error) {
                setData({
                    audioUrl: null,
                    metadata: null,
                    loading: false,
                    error: error instanceof Error ? error.message : "Failed to fetch audio",
                });
            }
        };

        fetchAudio();

        // Cleanup function to revoke object URL
        return () => {
            if (data.audioUrl) {
                URL.revokeObjectURL(data.audioUrl);
            }
        };
    }, [jobId, supabase]);

    return data;
}

export function useSheetMusicDisplay({ musicXml }: UseOSMDProps) {
    const [osmd, setOSMD] = useState<OpenSheetMusicDisplay | null>(null);

    const containerRef = useCallback((div: HTMLDivElement) => {
        if (div && !osmd) {
          // 1. Create OSMD instance when div becomes available
          const newOsmd = new OpenSheetMusicDisplay(div, {
            autoResize: true,
            backend: "svg", 
            drawTitle: true,
          });
          setOSMD(newOsmd);
        }
      }, [osmd]);

    useEffect(() => {
        if (!musicXml || !osmd) return;

        const renderSheet = async () => {
            try {
                await osmd.load(musicXml);
                await osmd.render();
            }
            catch (error) {
                console.error("Error rendering sheet music:", error);
            }
        }

        renderSheet();
    }, [musicXml, osmd]);

    return { containerRef, osmd };
}