import React, { useEffect, useRef } from 'react';
import { useSheetMusicDisplay } from '@/hooks/useSheetMusic';

interface MusicSheetViewerProps {
    musicXmlString?: string;
}

export default function MusicSheetViewer({ musicXmlString }: MusicSheetViewerProps) {
    const { containerRef, osmd } = useSheetMusicDisplay({ musicXml: musicXmlString });
    const divRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!osmd || !musicXmlString) return;

        setTimeout(() => {
            const svg = divRef.current?.querySelector('svg');
            console.log('svg', svg);
            if (!svg) return;

            svg.addEventListener('mouseover', (event: MouseEvent) => {
                const target = event.target as Element;
                
                // Look for vf-measure within staffline groups
                const measureElement = target.closest('.vf-measure');
                
                if (measureElement) {
                    console.log('Hovering on measure:', measureElement.id);
                }
            });
        }, 1000);

    }, [osmd, musicXmlString]);

    return (
        <div className="w-full min-h-full">
            <div ref={(div) => { 
                containerRef(div); 
                if (div) divRef.current = div; 
            }} className="w-full h-auto" />
        </div>
    );
}