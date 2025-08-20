import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { 
    Play, 
    Pause, 
    Square, 
    Volume2, 
    SkipForward, 
    SkipBack,
    FastForward,
    Rewind
} from 'lucide-react';

interface AudioPlayerProps {
    jobId: string;
    audioRef: React.RefObject<HTMLAudioElement | null>;
    metadata: any | null;
    goToNextMeasure?: () => void;
    goToPreviousMeasure?: () => void;
    goBack5Measures?: () => void;
    goForward5Measures?: () => void;
    seekToTime?: (timeInSeconds: number) => void;
    onPlay: () => Promise<void>;
    onPause: () => void;
    onStop: () => void;
}

export default function AudioPlayer({ 
    jobId, 
    audioRef, 
    metadata, 
    goToNextMeasure, 
    goToPreviousMeasure,
    goBack5Measures,
    goForward5Measures,
    seekToTime,
    onPlay,
    onPause,
    onStop
}: AudioPlayerProps) {
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [volume, setVolume] = useState(80);

    // Initialize audio element when audioUrl is available
    useEffect(() => {
        const audio = audioRef.current;
        if (!audio) return;

        // Create handlers with current state
        const handleEnded = () => setIsPlaying(false);
        const handlePause = () => setIsPlaying(false);
        const handlePlay = () => setIsPlaying(true);
        const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
        const handleLoadedMetadata = () => setDuration(audio.duration);

        // Add event listeners
        audio.addEventListener('ended', handleEnded);
        audio.addEventListener('pause', handlePause);
        audio.addEventListener('play', handlePlay);
        audio.addEventListener('timeupdate', handleTimeUpdate);
        audio.addEventListener('loadedmetadata', handleLoadedMetadata);

        return () => {
            // Clean up listeners from this specific audio element
            audio.removeEventListener('ended', handleEnded);
            audio.removeEventListener('pause', handlePause);
            audio.removeEventListener('play', handlePlay);
            audio.removeEventListener('timeupdate', handleTimeUpdate);
            audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
        };
    }, [audioRef.current]);

    // Reset state when audio element changes
    useEffect(() => {
        setIsPlaying(false);
        setCurrentTime(0);
        setDuration(0);
    }, [audioRef.current]);

    const formatTime = (time: number): string => {
        const minutes = Math.floor(time / 60);
        const seconds = Math.floor(time % 60);
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    };

    const progressPercentage = duration > 0 ? (currentTime / duration) * 100 : 0;

    const handleSeek = (value: number[]) => {
        if (!duration) return;
        
        const seekTime = (value[0] / 100) * duration;
        if (seekToTime) {
            seekToTime(seekTime);
        } else if (audioRef.current) {
            audioRef.current.currentTime = seekTime;
        }
    };

    return (
        <div className="w-full bg-gradient-to-br from-purple-100 to-blue-100 dark:bg-none dark:from-transparent dark:to-transparent dark:bg-background border-b border-gray-700 dark:border-gray-800 p-3">
            {/* Main Controls Row */}
            <div className="flex items-center justify-center space-x-4 mb-2">
                {/* Playback Controls */}
                <div className="flex items-center space-x-2">
                    {/* Go back 5 measures */}
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 hover:bg-gray-400 dark:hover:bg-gray-700"
                        disabled={!audioRef.current || !goBack5Measures}
                        onClick={goBack5Measures}
                        title="Go back 5 measures"
                    >
                        <Rewind className="h-3.5 w-3.5" />
                    </Button>
                    
                    {/* Previous measure */}
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 hover:bg-gray-400 dark:hover:bg-gray-700"
                        disabled={!audioRef.current || !goToPreviousMeasure}
                        onClick={goToPreviousMeasure}
                        title="Previous measure"
                    >
                        <SkipBack className="h-3.5 w-3.5" />
                    </Button>

                    {/* Play/Pause */}
                    <Button
                        variant="default"
                        size="sm"
                        onClick={isPlaying ? onPause : onPlay}
                        disabled={!audioRef.current}
                        className="h-8 w-8 p-0"
                    >
                        {isPlaying ? (
                            <Pause className="h-4 w-4" />
                        ) : (
                            <Play className="h-4 w-4" />
                        )}
                    </Button>

                    {/* Next measure */}
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 hover:bg-gray-400 dark:hover:bg-gray-700"
                        disabled={!audioRef.current || !goToNextMeasure}
                        onClick={goToNextMeasure}
                        title="Next measure"
                    >
                        <SkipForward className="h-3.5 w-3.5" />
                    </Button>

                    {/* Go forward 5 measures */}
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 hover:bg-gray-400 dark:hover:bg-gray-700"
                        disabled={!audioRef.current || !goForward5Measures}
                        onClick={goForward5Measures}
                        title="Go forward 5 measures"
                    >
                        <FastForward className="h-3.5 w-3.5" />
                    </Button>

                    {/* Stop */}
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={onStop}
                        disabled={!audioRef.current}
                        className="h-7 w-7 p-0 hover:bg-gray-400 dark:hover:bg-gray-700"
                    >
                        <Square className="h-3.5 w-3.5" />
                    </Button>
                </div>

                {/* Time Display */}
                <div className="flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-300 min-w-[100px]">
                    <span>{formatTime(currentTime)}</span>
                    <span>/</span>
                    <span>{formatTime(duration)}</span>
                </div>

                {/* Volume Control */}
                <div className="flex items-center space-x-2 min-w-[120px]">
                    <Volume2 className="h-4 w-4 text-gray-700 dark:text-gray-300" />
                    <Slider
                        value={[volume]}
                        onValueChange={(value) => setVolume(value[0])}
                        max={100}
                        step={1}
                        className="w-20"
                    />
                </div>

                {/* Measure Info */}
                {metadata && (
                    <div className="text-sm text-gray-700 dark:text-gray-300 ml-4">
                        {metadata.total_measures} measures
                    </div>
                )}
            </div>

            {/* Progress Bar Row */}
            <div className="w-full">
                <Slider
                    value={[progressPercentage]}
                    onValueChange={handleSeek}
                    max={100}
                    step={0.1}
                    className="w-full"
                />
            </div>
        </div>
    );
}