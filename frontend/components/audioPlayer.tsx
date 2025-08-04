import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Play, Pause, Square, Volume2 } from 'lucide-react';
import { useAudio } from '@/hooks/useAudio';

interface AudioPlayerProps {
    jobId: string;
}

export default function AudioPlayer({ jobId }: AudioPlayerProps) {
    const [isPlaying, setIsPlaying] = useState(false);
    const audioRef = useRef<HTMLAudioElement | null>(null);
    
    const { audioUrl, metadata, loading, error } = useAudio({ jobId });

    // Initialize audio element when audioUrl is available
    useEffect(() => {
        if (audioUrl) {
            const audio = new Audio(audioUrl);
            audioRef.current = audio;

            // Audio event listeners
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
    }, [audioUrl]);

    const play = async () => {
        if (audioRef.current) {
            try {
                await audioRef.current.play();
            } catch (error) {
                console.error('Error playing audio:', error);
            }
        }
    };

    const pause = () => {
        if (audioRef.current) {
            audioRef.current.pause();
        }
    };

    const stop = () => {
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
        }
        setIsPlaying(false);
    };

    if (loading) {
        return (
            <div className="flex items-center space-x-2 text-gray-500">
                <Volume2 className="h-4 w-4" />
                <span>Loading audio...</span>
            </div>
        );
    }

    if (error || !audioUrl) {
        return (
            <div className="flex items-center space-x-2 text-gray-500">
                <Volume2 className="h-4 w-4" />
                <span>No audio available</span>
            </div>
        );
    }

    return (
        <div className="flex items-center space-x-2">
            <Button
                variant="outline"
                size="sm"
                onClick={isPlaying ? pause : play}
                disabled={!audioUrl}
            >
                {isPlaying ? (
                    <Pause className="h-4 w-4" />
                ) : (
                    <Play className="h-4 w-4" />
                )}
            </Button>
            <Button 
                variant="outline" 
                size="sm" 
                onClick={stop}
                disabled={!audioUrl}
            >
                <Square className="h-4 w-4" />
            </Button>
            {metadata && (
                <span className="text-sm text-gray-500">
                    {metadata.total_measures} measures
                </span>
            )}
        </div>
    );
}