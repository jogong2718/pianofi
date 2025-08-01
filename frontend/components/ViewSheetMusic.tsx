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

        const attachListeners = async () => {
            try {
                // Wait for OSMD to finish rendering
                await osmd.render();
                
                // Small delay for DOM to be populated
                await new Promise(resolve => setTimeout(resolve, 100));
                
                const svg = divRef.current?.querySelector('svg');
                console.log('svg after render complete', svg);
                if (!svg) return;

                svg.addEventListener('mouseover', handleMouseOver);
                svg.addEventListener('mouseleave', handleMouseLeave);
            } catch (error) {
                console.error('OSMD render failed:', error);
            }
        };

        const findMeasurePair = (measureId: string) => {
            const svg = divRef.current?.querySelector('svg');
            if (!svg) return { trebleMeasure: null, bassMeasure: null };

            // Find which specific stafflines contain this measure ID
            const allStafflines = svg.querySelectorAll('[id*="Treble0"], [id*="Bass1"]');
            
            let trebleStaff = null;
            let bassStaff = null;
            
            // Find the treble and bass stafflines that contain this measure
            for (const staffline of allStafflines) {
                const measureInStaff = staffline.querySelector(`[id="${measureId}"]`);
                if (measureInStaff) {
                    if (staffline.id.includes('Treble0')) {
                        trebleStaff = staffline;
                    } else if (staffline.id.includes('Bass1')) {
                        bassStaff = staffline;
                    }
                }
            }
            
            if (!trebleStaff || !bassStaff) {
                console.log('Stafflines not found for measure', measureId);
                return { trebleMeasure: null, bassMeasure: null };
            }

            // Find measure with this ID in both stafflines
            const trebleMeasure = trebleStaff.querySelector(`[id="${measureId}"]`);
            const bassMeasure = bassStaff.querySelector(`[id="${measureId}"]`);

            return { trebleMeasure, bassMeasure };
        };

        const handleMouseOver = (event: MouseEvent) => {
            const target = event.target as Element;
            const measureElement = target.closest('.vf-measure');
            
            if (measureElement) {
                console.log('Hovering on measure:', measureElement.id);
                
                const { trebleMeasure, bassMeasure } = findMeasurePair(measureElement.id);
                
                if (trebleMeasure && bassMeasure) {
                    const firstPath = trebleMeasure.querySelector('path');
                    const allPaths = bassMeasure.querySelectorAll('path');
                    
                    if (firstPath && allPaths.length >= 5) {
                        const trebleBbox = firstPath.getBBox();
                        const bassBbox = allPaths[4].getBBox();
                        
                        // Remove any existing highlight
                        removeHighlight();
                        
                        // Create highlight rectangle
                        createHighlight(trebleBbox, bassBbox);
                    }
                }
            }
        };

        const createHighlight = (trebleBbox: DOMRect, bassBbox: DOMRect) => {
            const svg = divRef.current?.querySelector('svg');
            if (!svg) return;
            
            const highlight = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            
            // Calculate bounds spanning both corners
            const x = Math.min(trebleBbox.x, bassBbox.x);
            const y = trebleBbox.y;
            const width = Math.max(trebleBbox.width, bassBbox.width);
            const height = (bassBbox.y + bassBbox.height) - trebleBbox.y;
            
            highlight.setAttribute('x', x.toString());
            highlight.setAttribute('y', y.toString());
            highlight.setAttribute('width', width.toString());
            highlight.setAttribute('height', height.toString());
            highlight.setAttribute('fill', 'rgba(0, 123, 255, 0.2)');
            highlight.setAttribute('stroke', 'rgba(0, 123, 255, 0.5)');
            highlight.setAttribute('stroke-width', '2');
            highlight.setAttribute('class', 'measure-highlight');
            highlight.setAttribute('pointer-events', 'none');
            
            svg.appendChild(highlight);
        };

        const removeHighlight = () => {
            const svg = divRef.current?.querySelector('svg');
            if (!svg) return;
            
            const existingHighlight = svg.querySelector('.measure-highlight');
            if (existingHighlight) {
                existingHighlight.remove();
            }
        };

        // Add mouse leave handler to remove highlight
        const handleMouseLeave = () => {
            removeHighlight();
        };

        attachListeners();
        
        // Still listen for resize events
        window.addEventListener('resize', attachListeners);

        return () => {
            window.removeEventListener('resize', attachListeners);
        };

    }, [osmd, musicXmlString]);

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