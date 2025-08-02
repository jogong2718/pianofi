import React, { useState, useEffect } from 'react';
import * as Tone from 'tone';
import { Midi } from '@tonejs/midi';
import { Button } from '@/components/ui/button';
import { Play, Pause, Square, Volume2 } from 'lucide-react';

interface MidiPlayerProps {
    midi: Midi | null;
}

export default function MidiPlayer({ midi }: MidiPlayerProps) {
    const [isPlaying, setIsPlaying] = useState(false);
    const [synth, setSynth] = useState<Tone.Sampler | null>(null);

    useEffect(() => {
        const sampler = new Tone.Sampler({
            urls: {
                C1: 'C1.mp3', C2: 'C2.mp3', C3: 'C3.mp3',
                C4: 'C4.mp3', C5: 'C5.mp3', C6: 'C6.mp3', C7: 'C7.mp3',
                'F#1': 'Fs1.mp3', 'F#2': 'Fs2.mp3', 'F#3': 'Fs3.mp3',
                'F#4': 'Fs4.mp3', 'F#5': 'Fs5.mp3', 'F#6': 'Fs6.mp3'
            },
            release: 1,
            baseUrl: 'https://tonejs.github.io/audio/salamander/',
        }).toDestination();

        Tone.loaded().then(() => setSynth(sampler));
        return () => {
            sampler.dispose();
        };
    }, []);

    const play = async () => {
        if (!midi || !synth) return;

        await Tone.start();
        
        // Clear any existing events
        Tone.Transport.cancel();
        
        // Schedule MIDI notes
        midi.tracks.forEach(track => {
            track.notes.forEach(note => {
                Tone.Transport.schedule((time) => {
                    synth.triggerAttackRelease(
                        note.name,
                        note.duration,
                        time,
                        note.velocity
                    );
                }, note.time);
            });
        });

        Tone.Transport.start();
        setIsPlaying(true);
    };

    const pause = () => {
        Tone.Transport.pause();
        setIsPlaying(false);
    };

    const stop = () => {
        Tone.Transport.stop();
        Tone.Transport.cancel();
        setIsPlaying(false);
    };

    if (!midi) {
        return (
            <div className="flex items-center space-x-2 text-gray-500">
                <Volume2 className="h-4 w-4" />
                <span>No audio available</span>
            </div>
        );
    }

    return (
        <div className="flex items-center space-x-2">
            <Button
                variant="outline"
                size="sm"
                onClick={isPlaying ? pause : play}
            >
                {isPlaying ? (
                    <Pause className="h-4 w-4" />
                ) : (
                    <Play className="h-4 w-4" />
                )}
            </Button>
            <Button variant="outline" size="sm" onClick={stop}>
                <Square className="h-4 w-4" />
            </Button>
        </div>
    );
}