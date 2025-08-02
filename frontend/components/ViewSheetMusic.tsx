import React, { useEffect, useRef, useState } from 'react';
import { useSheetMusicDisplay } from '@/hooks/useSheetMusic';

interface MusicSheetViewerProps {
    musicXmlString?: string;
}

interface MeasureBounds {
    treble: Element;
    bass: Element;
    id: string;
    combinedBbox: DOMRect;
}

export default function MusicSheetViewer({ musicXmlString }: MusicSheetViewerProps) {
    const { containerRef, osmd } = useSheetMusicDisplay({ musicXml: musicXmlString });
    const divRef = useRef<HTMLDivElement>(null);

    const [measureBounds, setMeasureBounds] = useState<MeasureBounds[]>([]);
    const [selectedMeasure, setSelectedMeasure] = useState<string | null>(null);
    const [hoveredMeasure, setHoveredMeasure] = useState<string | null>(null);

    const precomputeMeasureBounds = async () => {
        const svg = divRef.current?.querySelector('svg');
        if (!svg) return;

        const allMeasures = svg.querySelectorAll('.vf-measure');
        console.log('allMeasures', allMeasures);

        const measureDict: { [id: string]: { treble?: Element, bass?: Element } } = {};

        for (const measure of allMeasures) {
            const id = measure.id;

            if (!measureDict[id]) {
                measureDict[id] = {};
            }

            // Determine if treble or bass based on position/parent
            const staffline = measure.closest('[id*="Treble0"], [id*="Bass1"]');
            if (staffline?.id.includes('Treble0')) {
                measureDict[id].treble = measure;
            } else if (staffline?.id.includes('Bass1')) {
                measureDict[id].bass = measure;
            }
        }

        console.log('measureDict', measureDict);

        // O(m) - create bounds from dictionary using first and fifth paths
        const bounds: MeasureBounds[] = [];
        for (const [id, elements] of Object.entries(measureDict)) {
            if (elements.treble && elements.bass) {
                const firstPath = elements.treble.querySelector('path');
                const allBassPaths = elements.bass.querySelectorAll('path');
                const fifthPath = allBassPaths[4];
                
                if (firstPath && fifthPath) {
                    const trebleBbox = firstPath.getBBox();
                    const bassBbox = fifthPath.getBBox();

                    const x = Math.min(trebleBbox.x, bassBbox.x);
                    const y = trebleBbox.y; 
                    const width = Math.max(trebleBbox.width, bassBbox.width);
                    const height = (bassBbox.y + bassBbox.height) - trebleBbox.y;

                    bounds.push({
                        treble: elements.treble,
                        bass: elements.bass,
                        id,
                        combinedBbox: new DOMRect(x, y, width, height)
                    });
                } else {
                    console.warn(`Missing paths for measure ${id}: treble first path: ${!!firstPath}, bass fifth path: ${!!fifthPath}`);
                }
            }
        }

        console.log('Precomputed bounds for', bounds.length, 'measures');
        console.log('bounds', bounds);
        setMeasureBounds(bounds);
    }

    // Fast measure detection using precomputed bounds - O(m) where m = number of measures
    const findMeasureFromCoordinates = (event: MouseEvent): MeasureBounds | null => {
        const svg = divRef.current?.querySelector('svg');
        if (!svg) return null;
        
        // Get mouse position relative to SVG
        const svgRect = svg.getBoundingClientRect();
        const x = event.clientX - svgRect.left;
        const y = event.clientY - svgRect.top;
        // Check precomputed bounds - much faster than DOM queries
        for (const bound of measureBounds) {
            const bbox = bound.combinedBbox;
            if (x >= bbox.left && x <= bbox.right && 
                y >= bbox.top && y <= bbox.bottom) {
                console.log('found measure', bound.id);
                return bound;
            }
        }
        
        return null;
    };

    const handleMouseOver = (event: MouseEvent) => {
        const measureBound = findMeasureFromCoordinates(event);
        
        if (measureBound && measureBound.id !== selectedMeasure) {
            if (hoveredMeasure !== measureBound.id) {
                setHoveredMeasure(measureBound.id);
                removeHighlight('hover');
                createHighlight(measureBound, false); // hover highlight
            }
        } else if (!measureBound && hoveredMeasure) {
            setHoveredMeasure(null);
            removeHighlight('hover');
        }
    };

    const handleClick = (event: MouseEvent) => {
        const measureBound = findMeasureFromCoordinates(event);
        
        if (measureBound) {
            setSelectedMeasure(measureBound.id);
            setHoveredMeasure(null); 
            removeHighlight(); 
            createHighlight(measureBound, true); 
            console.log('Selected measure:', measureBound.id);
        }
    };

    const createHighlight = (measureBound: MeasureBounds, persistent: boolean = false) => {
        const svg = divRef.current?.querySelector('svg');
        if (!svg) return;
        
        const highlight = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        const bbox = measureBound.combinedBbox;
        
        highlight.setAttribute('x', bbox.x.toString());
        highlight.setAttribute('y', bbox.y.toString());
        highlight.setAttribute('width', bbox.width.toString());
        highlight.setAttribute('height', bbox.height.toString());
        
        if (persistent) {
            highlight.setAttribute('fill', 'rgba(255, 165, 0, 0.3)'); // Orange
            highlight.setAttribute('stroke', 'rgba(255, 165, 0, 0.8)');
            highlight.setAttribute('class', 'measure-highlight-persistent');
        } else {
            highlight.setAttribute('fill', 'rgba(0, 123, 255, 0.2)'); // Blue
            highlight.setAttribute('stroke', 'rgba(0, 123, 255, 0.5)');
            highlight.setAttribute('class', 'measure-highlight-hover');
        }
        
        highlight.setAttribute('stroke-width', '2');
        highlight.setAttribute('pointer-events', 'none');
        
        svg.appendChild(highlight);
    };

    const removeHighlight = (type?: 'hover' | 'persistent') => {
        const svg = divRef.current?.querySelector('svg');
        if (!svg) return;
        
        if (!type || type === 'hover') {
            const hoverHighlight = svg.querySelector('.measure-highlight-hover');
            if (hoverHighlight) hoverHighlight.remove();
        }
        
        if (!type || type === 'persistent') {
            const persistentHighlight = svg.querySelector('.measure-highlight-persistent');
            if (persistentHighlight) persistentHighlight.remove();
        }
    };

    const handleMouseLeave = () => {
        setHoveredMeasure(null);
        removeHighlight('hover');
    };

    // Update attachListeners to add event listeners
    const attachListeners = async () => {
        try {
            await osmd?.render();
            await new Promise(resolve => setTimeout(resolve, 100));
            
            const svg = divRef.current?.querySelector('svg');
            console.log('svg after render complete', svg);
            if (!svg) return;

            precomputeMeasureBounds();

        } catch (error) {
            console.error('OSMD render failed:', error);
        }
    };

    // Update cleanup in useEffect
    useEffect(() => {
        if (!osmd || !musicXmlString) return;
        attachListeners();

        window.addEventListener('resize', attachListeners);

        return () => {
            const svg = divRef.current?.querySelector('svg');
            if (svg) {
                svg.removeEventListener('mousemove', handleMouseOver);
                svg.removeEventListener('mouseleave', handleMouseLeave);
                svg.removeEventListener('click', handleClick);
            }
            window.removeEventListener('resize', attachListeners);
        }
    }, [osmd, musicXmlString]);

    // Separate useEffect for event listeners that waits for measureBounds
    useEffect(() => {
        if (measureBounds.length === 0) return; 

        const svg = divRef.current?.querySelector('svg');
        if (!svg) return;

        console.log('Adding event listeners with', measureBounds.length, 'bounds');

        svg.addEventListener('mousemove', handleMouseOver);
        svg.addEventListener('mouseleave', handleMouseLeave);
        svg.addEventListener('click', handleClick);

        return () => {
            svg.removeEventListener('mousemove', handleMouseOver);
            svg.removeEventListener('mouseleave', handleMouseLeave);
            svg.removeEventListener('click', handleClick);
        };
    }, [measureBounds]); 

    

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