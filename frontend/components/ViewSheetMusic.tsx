import React, { useEffect, useRef } from 'react';
import { useSheetMusicDisplay } from '@/hooks/useSheetMusic';
import { usePlayback } from '@/hooks/usePlayback';

interface MusicSheetViewerProps {
    musicXmlString?: string;
    audioRef: React.RefObject<HTMLAudioElement | null>;
    metadata: any | null;
}

export default function MusicSheetViewer({ musicXmlString, audioRef, metadata }: MusicSheetViewerProps) {
    const { containerRef, osmd } = useSheetMusicDisplay({ musicXml: musicXmlString });
    const divRef = useRef<HTMLDivElement>(null);

    
    const {
        measureBounds,
        handleMouseOver,
        handleClick,
        handleMouseLeave,
        recomputeBounds
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
                await osmd.render();           // ← First re-render OSMD
                await recomputeBounds();       // ← Then recompute bounds
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

        // Add resize listener to recompute measure bounds
        window.addEventListener('resize', handleResize);

        return () => {
            svg.removeEventListener('mousemove', handleMouseOver);
            svg.removeEventListener('mouseleave', handleMouseLeave);
            svg.removeEventListener('click', handleClick);
            window.removeEventListener('resize', handleResize);
        };
    }, [measureBounds, handleMouseOver, handleMouseLeave, handleClick, osmd]);

    return (
        <div className="w-full min-h-full">
            <div ref={(div) => {
                if (div) {
                    containerRef(div);
                    divRef.current = div;
                }
            }} className="w-full h-auto" />
        </div>
    );
}