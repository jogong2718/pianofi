import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Play, Pause, Square, Volume2 } from 'lucide-react';
import { useAudio } from '@/hooks/useAudio';

interface AudioPlayerProps {
    jobId: string;
    audioRef: React.RefObject<HTMLAudioElement | null>;
    metadata: any | null;
}

export default function AudioPlayer({ jobId, audioRef, metadata }: AudioPlayerProps) {
    const [isPlaying, setIsPlaying] = useState(false);


    // Initialize audio element when audioUrl is available
    useEffect(() => {
        if (audioRef.current) {
            const audio = audioRef.current;

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
    }, [audioRef]);

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

    return (
        <div className="flex items-center space-x-2">
            <Button
                variant="outline"
                size="sm"
                onClick={isPlaying ? pause : play}
                disabled={!audioRef}
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
                disabled={!audioRef}
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