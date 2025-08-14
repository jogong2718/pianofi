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
        goForward5Measures
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

    return (
        <div className="w-full min-h-full bg-gray-900 dark:bg-black">
            <AudioPlayer
                jobId={jobId}
                audioRef={audioRef}
                metadata={metadata}
                goToNextMeasure={goToNextMeasure}
                goToPreviousMeasure={goToPreviousMeasure} goBack5Measures={goBack5Measures} goForward5Measures={goForward5Measures}
            />
            <div className="w-full bg-gray-900 dark:bg-black">
                <div ref={(div) => {
                    if (div) {
                        containerRef(div);
                        divRef.current = div;
                    }
                }} className="w-full max-w-6xl mx-auto h-auto bg-white dark:bg-gray-50" />
            </div>
        </div>
    );
}