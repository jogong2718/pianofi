import React, { useEffect, useRef } from 'react';
import { useSheetMusicDisplay } from '@/hooks/useSheetMusic';
import { usePlayback } from '@/hooks/usePlayback';
import AudioPlayer from './audioPlayer';

interface MusicSheetViewerProps {
    jobId: string;
    musicXmlString?: string;
    audioRef: React.RefObject<HTMLAudioElement | null>;
    metadata: any | null;
}

export default function MusicSheetViewer({ jobId, musicXmlString, audioRef, metadata }: MusicSheetViewerProps) {
    const { containerRef, osmd } = useSheetMusicDisplay({ musicXml: musicXmlString });
    const divRef = useRef<HTMLDivElement>(null);

    const {
        measureBounds,
        handleMouseOver,
        handleClick,
        handleMouseLeave,
        recomputeBounds,
        goToNextMeasure,
        goToPreviousMeasure,
        goBack5Measures,
        goForward5Measures,
        seekToTime,
        play,
        pause,
        stop
    } = usePlayback({
        audioRef,
        metadata,
        osmd,
        svgContainer: divRef.current
    });

    // Update the resize handler
    const handleResize = () => {
        setTimeout(async () => {
            if (osmd && divRef.current) {
                await osmd.render();
                await recomputeBounds();
            }
        }, 100);
    };

    // Add event listeners when measureBounds are ready
    useEffect(() => {
        if (measureBounds.length === 0) return;

        const svg = divRef.current?.querySelector('svg');
        if (!svg) return;

        svg.addEventListener('mousemove', handleMouseOver);
        svg.addEventListener('mouseleave', handleMouseLeave);
        svg.addEventListener('click', handleClick);

        window.addEventListener('resize', handleResize);

        return () => {
            svg.removeEventListener('mousemove', handleMouseOver);
            svg.removeEventListener('mouseleave', handleMouseLeave);
            svg.removeEventListener('click', handleClick);
            window.removeEventListener('resize', handleResize);
        };
    }, [measureBounds, handleMouseOver, handleMouseLeave, handleClick, osmd]);

    // Download rendered osmd as png
    const handleDownloadPng = () => {
        const svgElement = divRef.current?.querySelector('svg');
        if (!svgElement) return;

        const svgData = new XMLSerializer().serializeToString(svgElement);
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
        const url = URL.createObjectURL(svgBlob);

        img.onload = () => {
            canvas.width = img.width;
            canvas.height = img.height;
            if (ctx) ctx.drawImage(img, 0, 0);
            URL.revokeObjectURL(url);
            const pngUrl = canvas.toDataURL('image/png');
            const link = document.createElement('a');
            link.href = pngUrl;
            link.download = 'sheet_music.png';
            link.click();
        };

        img.src = url;
    };

    return (
        <div className="h-full flex flex-col bg-gray-900 dark:bg-black">
            {/* Audio Player - Fixed at top */}
            <div className="flex-shrink-0">
                <AudioPlayer
                    key={jobId}
                    jobId={jobId}
                    audioRef={audioRef}
                    metadata={metadata}
                    goToNextMeasure={goToNextMeasure}
                    goToPreviousMeasure={goToPreviousMeasure}
                    goBack5Measures={goBack5Measures}
                    goForward5Measures={goForward5Measures}
                    seekToTime={seekToTime}
                    onPlay={play}
                    onPause={pause}
                    onStop={stop}
                />
            </div>
            
            {/* Sheet Music - Scrollable */}
            <div className="flex-1 overflow-y-auto bg-slate-300 dark:bg-black">
                <div className="w-full max-w-6xl mx-auto bg-white dark:bg-gray-50 min-h-full">
                    {/* Added download button */}
                    <div className="flex justify-end p-2">
                        <button
                            onClick={handleDownloadPng}
                            className="px-3 py-1 text-sm text-white bg-blue-600 rounded hover:bg-blue-700"
                        >
                            Download PNG
                        </button>
                    </div>

                    <div ref={(div) => {
                        if (div) {
                            containerRef(div);
                            divRef.current = div;
                        }
                    }} className="w-full h-auto" />
                </div>
            </div>
        </div>
    );
}
