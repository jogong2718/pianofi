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
    recomputeBounds: () => Promise<void>;
    goToNextMeasure: () => void;
    goToPreviousMeasure: () => void;
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

        const measureDict: { [id: string]: { treble?: Element, bass?: Element } } = {};

        for (const measure of allMeasures) {
            const id = measure.id;

            if (!measureDict[id]) {
                measureDict[id] = {};
            }

            const staffline = measure.closest('[id$="0-1"], [id$="1-1"]');
            if (staffline?.id.endsWith('0-1')) { // treble
                measureDict[id].treble = measure;
            } else if (staffline?.id.endsWith('1-1')) { // bass
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
                return bound;
            }
        }
        
        return null;
    }, [measureBounds, svgContainer]);

    // Helper function to find which measure is playing at current time
    const findMeasureFromTime = useCallback((currentTime: number): string | null => {
        if (!metadata?.measures) return null;

        const measureEntries = Object.entries(metadata.measures);
        
        if (measureEntries.length === 0) return null;
        if (currentTime < measureEntries[0][1].start) return null;
        
        let left = 0;
        let right = measureEntries.length - 1;
        let result = null;

        while (left <= right) {
            const mid = Math.floor((left + right) / 2);
            const [measureId, measureData] = measureEntries[mid];

            if (currentTime >= measureData.start && currentTime < measureData.end) {
                return measureId;
            } else if (currentTime < measureData.start) {
                right = mid - 1;
            } else {
                result = measureId; 
                left = mid + 1;
            }
        }

        return result;
    }, [metadata]);

    // Pure highlighting function - responds to state changes
    const updateHighlights = useCallback(() => {
        const svg = svgContainer?.querySelector('svg');
        if (!svg) return;
        
        // Remove all existing highlights
        svg.querySelectorAll('.measure-highlight-hover, .measure-highlight-selected').forEach(h => h.remove());
        
        // Add hover highlight (lower priority)
        if (hoveredMeasure && hoveredMeasure !== selectedMeasure) {
            const hoverBound = measureBounds.find(m => m.id === hoveredMeasure);
            if (hoverBound) {
                createHighlight(hoverBound, 'hover');
            }
        }
        
        // Add selected highlight (higher priority)
        if (selectedMeasure) {
            const selectedBound = measureBounds.find(m => m.id === selectedMeasure);
            if (selectedBound) {
                createHighlight(selectedBound, 'selected');
            }
        }
    }, [selectedMeasure, hoveredMeasure, measureBounds, svgContainer]);

    // Updated highlight creation with types
    const createHighlight = useCallback((measureBound: MeasureBounds, type: 'hover' | 'selected') => {
        const svg = svgContainer?.querySelector('svg');
        if (!svg) return;
        
        const highlight = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        const bbox = measureBound.combinedBbox;
        
        highlight.setAttribute('x', bbox.x.toString());
        highlight.setAttribute('y', bbox.y.toString());
        highlight.setAttribute('width', bbox.width.toString());
        highlight.setAttribute('height', bbox.height.toString());
        highlight.setAttribute('stroke-width', '2');
        highlight.setAttribute('pointer-events', 'none');
        
        if (type === 'selected') {
            highlight.setAttribute('fill', 'rgba(34, 197, 94, 0.3)');  // Green for playing/selected
            highlight.setAttribute('stroke', 'rgba(34, 197, 94, 0.8)');
            highlight.setAttribute('class', 'measure-highlight-selected');
        } else {
            highlight.setAttribute('fill', 'rgba(0, 123, 255, 0.2)');  // Blue for hover
            highlight.setAttribute('stroke', 'rgba(0, 123, 255, 0.5)');
            highlight.setAttribute('class', 'measure-highlight-hover');
        }
        
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

    // Simplified click handler - ONLY sets state
    const handleClick = useCallback((event: MouseEvent) => {
        const measureBound = findMeasureFromCoordinates(event);
        if (!measureBound) return;
        
        const wasPlaying = audioRef.current && !audioRef.current.paused;
        
        // Set selected measure
        setSelectedMeasure(measureBound.id);
        setHoveredMeasure(null);
        
        // Jump audio to this measure
        if (audioRef.current && metadata?.measures) {
            const measureData = metadata.measures[measureBound.id];
            if (measureData) {
                audioRef.current.currentTime = measureData.start;
                
                // Continue playing if it was already playing
                if (wasPlaying) {
                    audioRef.current.play();
                }
            }
        }
    }, [findMeasureFromCoordinates, audioRef, metadata]);

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
        if (!audioRef.current) return;
        
        // Default to first measure if none selected
        if (!selectedMeasure) {
            setSelectedMeasure("1");
            if (metadata?.measures?.["1"]) {
                audioRef.current.currentTime = metadata.measures["1"].start;
            }
        }
        
        try {
            await audioRef.current.play();
        } catch (error) {
            console.error('Error playing audio:', error);
        }
    }, [audioRef, selectedMeasure, metadata]);

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

    // Simplified playMeasure function
    const playMeasure = useCallback((measureId: string) => {
        setSelectedMeasure(measureId);
        
        if (audioRef.current && metadata?.measures) {
            const measureData = metadata.measures[measureId];
            if (measureData) {
                audioRef.current.currentTime = measureData.start;
                play();
            }
        }
    }, [audioRef, metadata, play]);

    // Add these functions to usePlayback:
    const goToNextMeasure = useCallback(() => {
        if (!selectedMeasure || !metadata?.measures) return;
        const nextMeasure = (parseInt(selectedMeasure) + 1).toString();
        if (metadata.measures[nextMeasure]) {
            playMeasure(nextMeasure);
        }
    }, [selectedMeasure, metadata, playMeasure]);

    const goToPreviousMeasure = useCallback(() => {
        if (!selectedMeasure || !metadata?.measures) return;
        const prevMeasure = (parseInt(selectedMeasure) - 1).toString();
        if (metadata.measures[prevMeasure]) {
            playMeasure(prevMeasure);
        }
    }, [selectedMeasure, metadata, playMeasure]);

    // Auto-update selectedMeasure as audio plays
    useEffect(() => {
        const audio = audioRef.current;
        if (!audio || !metadata?.measures) return;

        const handleTimeUpdate = () => {
            // Only update if audio is actually playing
            if (!audio.paused) {
                const currentTime = audio.currentTime;
                const currentMeasure = findMeasureFromTime(currentTime);
                if (currentMeasure && currentMeasure !== selectedMeasure) {
                    console.log(`Measure changed: ${selectedMeasure} → ${currentMeasure} (time: ${currentTime.toFixed(2)}s)`);
                    setSelectedMeasure(currentMeasure);
                }
            }
        };

        audio.addEventListener('timeupdate', handleTimeUpdate);
        return () => audio.removeEventListener('timeupdate', handleTimeUpdate);
    }, [audioRef, metadata, findMeasureFromTime, selectedMeasure]);

    // Update highlights whenever state changes
    useEffect(() => {
        updateHighlights();
    }, [updateHighlights]);

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
        playMeasure,
        recomputeBounds: precomputeMeasureBounds,
        goToNextMeasure,
        goToPreviousMeasure,
    };
} 