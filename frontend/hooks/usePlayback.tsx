import { useState, useEffect, useCallback, useRef } from 'react';
import { OpenSheetMusicDisplay } from "opensheetmusicdisplay";

interface UsePlaybackProps {
    audioRef: React.RefObject<HTMLAudioElement | null>;
    metadata: any | null;
    osmd?: OpenSheetMusicDisplay | null;
    svgContainer?: HTMLDivElement | null;
}

interface MeasureBounds {
    treble: Element;
    bass: Element;
    id: string;
    combinedBbox: DOMRect;
}

interface PlaybackData {
    // Measure interaction state
    measureBounds: MeasureBounds[];
    selectedMeasure: string | null;
    hoveredMeasure: string | null;
    
    // Event handlers
    handleMouseOver: (event: MouseEvent) => void;
    handleClick: (event: MouseEvent) => void;
    handleMouseLeave: () => void;
    
    // Audio controls
    play: () => Promise<void>;
    pause: () => void;
    stop: () => void;
    playMeasure: (measureId: string) => void;
}

export function usePlayback({ audioRef, metadata, osmd, svgContainer }: UsePlaybackProps): PlaybackData {
    // Measure interaction state
    const [measureBounds, setMeasureBounds] = useState<MeasureBounds[]>([]);
    const [selectedMeasure, setSelectedMeasure] = useState<string | null>(null);
    const [hoveredMeasure, setHoveredMeasure] = useState<string | null>(null);

    const measureTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    // Precompute measure bounds
    const precomputeMeasureBounds = useCallback(async () => {
        const svg = svgContainer?.querySelector('svg');
        if (!svg) return;

        const allMeasures = svg.querySelectorAll('.vf-measure');
        console.log('allMeasures', allMeasures);

        const measureDict: { [id: string]: { treble?: Element, bass?: Element } } = {};

        for (const measure of allMeasures) {
            const id = measure.id;

            if (!measureDict[id]) {
                measureDict[id] = {};
            }

            const staffline = measure.closest('[id*="Treble0"], [id*="Bass1"]');
            if (staffline?.id.includes('Treble0')) {
                measureDict[id].treble = measure;
            } else if (staffline?.id.includes('Bass1')) {
                measureDict[id].bass = measure;
            }
        }

        console.log('measureDict', measureDict);

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
        setMeasureBounds(bounds);
    }, [svgContainer]);

    // Find measure from coordinates
    const findMeasureFromCoordinates = useCallback((event: MouseEvent): MeasureBounds | null => {
        const svg = svgContainer?.querySelector('svg');
        if (!svg) return null;
        
        const svgRect = svg.getBoundingClientRect();
        const x = event.clientX - svgRect.left;
        const y = event.clientY - svgRect.top;
        
        for (const bound of measureBounds) {
            const bbox = bound.combinedBbox;
            if (x >= bbox.left && x <= bbox.right && 
                y >= bbox.top && y <= bbox.bottom) {
                console.log('found measure', bound.id);
                return bound;
            }
        }
        
        return null;
    }, [measureBounds, svgContainer]);

    // Create highlight
    const createHighlight = useCallback((measureBound: MeasureBounds, persistent: boolean = false) => {
        const svg = svgContainer?.querySelector('svg');
        if (!svg) return;
        
        const highlight = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        const bbox = measureBound.combinedBbox;
        
        highlight.setAttribute('x', bbox.x.toString());
        highlight.setAttribute('y', bbox.y.toString());
        highlight.setAttribute('width', bbox.width.toString());
        highlight.setAttribute('height', bbox.height.toString());
        
        if (persistent) {
            highlight.setAttribute('fill', 'rgba(255, 165, 0, 0.3)');
            highlight.setAttribute('stroke', 'rgba(255, 165, 0, 0.8)');
            highlight.setAttribute('class', 'measure-highlight-persistent');
        } else {
            highlight.setAttribute('fill', 'rgba(0, 123, 255, 0.2)');
            highlight.setAttribute('stroke', 'rgba(0, 123, 255, 0.5)');
            highlight.setAttribute('class', 'measure-highlight-hover');
        }
        
        highlight.setAttribute('stroke-width', '2');
        highlight.setAttribute('pointer-events', 'none');
        
        svg.appendChild(highlight);
    }, [svgContainer]);

    // Remove highlight
    const removeHighlight = useCallback((type?: 'hover' | 'persistent') => {
        const svg = svgContainer?.querySelector('svg');
        if (!svg) return;
        
        if (!type || type === 'hover') {
            const hoverHighlight = svg.querySelector('.measure-highlight-hover');
            if (hoverHighlight) hoverHighlight.remove();
        }
        
        if (!type || type === 'persistent') {
            const persistentHighlight = svg.querySelector('.measure-highlight-persistent');
            if (persistentHighlight) persistentHighlight.remove();
        }
    }, [svgContainer]);

    // Event handlers
    const handleMouseOver = useCallback((event: MouseEvent) => {
        const measureBound = findMeasureFromCoordinates(event);
        
        if (measureBound && measureBound.id !== selectedMeasure) {
            if (hoveredMeasure !== measureBound.id) {
                setHoveredMeasure(measureBound.id);
                removeHighlight('hover');
                createHighlight(measureBound, false);
            }
        } else if (!measureBound && hoveredMeasure) {
            setHoveredMeasure(null);
            removeHighlight('hover');
        }
    }, [findMeasureFromCoordinates, selectedMeasure, hoveredMeasure, removeHighlight, createHighlight]);

    const handleClick = useCallback((event: MouseEvent) => {
        const measureBound = findMeasureFromCoordinates(event);
        
        if (measureBound) {
            setSelectedMeasure(measureBound.id);
            setHoveredMeasure(null); 
            removeHighlight(); 
            createHighlight(measureBound, true); 
            console.log('Selected measure:', measureBound.id);
            
            // Auto-play the measure
            playMeasure(measureBound.id);
        }
    }, [findMeasureFromCoordinates, removeHighlight, createHighlight]);

    const handleMouseLeave = useCallback(() => {
        setHoveredMeasure(null);
        removeHighlight('hover');
    }, [removeHighlight]);

    // Initialize measure bounds when OSMD is ready
    useEffect(() => {
        if (!osmd || !svgContainer) return;

        const initializeMeasures = async () => {
            try {
                await osmd.render();
                await new Promise(resolve => setTimeout(resolve, 100));
                precomputeMeasureBounds();
            } catch (error) {
                console.error('OSMD render failed:', error);
            }
        };

        initializeMeasures();
    }, [osmd, svgContainer, precomputeMeasureBounds]);

    // Audio control functions
    const play = useCallback(async () => {
        if (audioRef.current) {
            try {
                await audioRef.current.play();
            } catch (error) {
                console.error('Error playing audio:', error);
            }
        }
    }, [audioRef]);

    const pause = useCallback(() => {
        if (audioRef.current) {
            audioRef.current.pause();
        }
    }, [audioRef]);

    const stop = useCallback(() => {
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
        }
    }, [audioRef]);

    const playMeasure = useCallback((measureId: string) => {
        if (audioRef.current && metadata?.measures) {
            const measureData = metadata.measures[measureId];
            if (measureData) {
                // 1. Stop current audio and clear any existing timeout
                audioRef.current.pause();
                if (measureTimeoutRef.current) {
                    clearTimeout(measureTimeoutRef.current);
                    measureTimeoutRef.current = null;
                }
                
                // 2. Set new position and play
                audioRef.current.currentTime = measureData.start;
                play();
                
                // 3. Set new timeout to stop at measure end
                measureTimeoutRef.current = setTimeout(() => {
                    pause();
                    measureTimeoutRef.current = null;
                }, (measureData.end - measureData.start) * 1000);
            }
        }
    }, [audioRef, metadata, play, pause]);

    // Cleanup timeout on unmount
    useEffect(() => {
        return () => {
            if (measureTimeoutRef.current) {
                clearTimeout(measureTimeoutRef.current);
            }
        };
    }, []);

    return {
        measureBounds,
        selectedMeasure,
        hoveredMeasure,
        handleMouseOver,
        handleClick,
        handleMouseLeave,
        play,
        pause,
        stop,
        playMeasure
    };
} 