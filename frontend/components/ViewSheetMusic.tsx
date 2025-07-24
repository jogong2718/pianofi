import React, { useEffect, useRef } from 'react';
import { useSheetMusicDisplay } from '@/hooks/useSheetMusic';

interface MusicSheetViewerProps {
    musicXmlString?: string;
}

export default function MusicSheetViewer({ musicXmlString }: MusicSheetViewerProps) {

    const { containerRef, osmd } = useSheetMusicDisplay({ musicXml: musicXmlString });

    return (
        <div className="w-full h-auto">
            <div ref={containerRef} className="w-full h-auto" />
        </div>
    );
}