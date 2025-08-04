import { useState, useEffect, useRef } from 'react';
import { createClient } from "@/lib/supabase/client";

interface UseAudioProps {
    jobId: string;
}

interface AudioData {
    audioUrl: string | null;
    metadata: any | null;
    loading: boolean;
    error: string | null;
    audioRef: React.RefObject<HTMLAudioElement | null>;
    isPlaying: boolean;
}

export function useAudio({ jobId }: UseAudioProps): AudioData {
    const [data, setData] = useState({
        audioUrl: null as string | null,
        metadata: null as any,
        loading: true,
        error: null as string | null,
    });

    const [isPlaying, setIsPlaying] = useState(false);
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const supabase = createClient();

    // Fetch audio data
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

                const audioBlob = await response.blob();
                const audioUrl = URL.createObjectURL(audioBlob);

                const metadataHeader = response.headers.get('X-Audio-Metadata');
                console.log('response', response);
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

        return () => {
            if (data.audioUrl) {
                URL.revokeObjectURL(data.audioUrl);
            }
        };
    }, [jobId, supabase]);

    // Initialize audio element
    useEffect(() => {
        if (data.audioUrl) {
            const audio = new Audio(data.audioUrl);
            audioRef.current = audio;

            audio.addEventListener('ended', () => setIsPlaying(false));
            audio.addEventListener('pause', () => setIsPlaying(false));
            audio.addEventListener('play', () => setIsPlaying(true));

            return () => {
                audio.pause();
                audio.removeEventListener('ended', () => setIsPlaying(false));
                audio.removeEventListener('pause', () => setIsPlaying(false));
                audio.removeEventListener('play', () => setIsPlaying(true));
                audioRef.current = null;
            };
        }
    }, [data.audioUrl]);

    return {
        ...data,
        audioRef,
        isPlaying
    };
}