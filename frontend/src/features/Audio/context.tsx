import React, { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { useToast } from '@/components/ui';

type AudioState = 'play' | 'pause'

type AudioContext = {
  time: number;
  duration?: number;
  state: AudioState;
  stopTime?: number;
  source?: string;
  setStopTime: (stopTime: number) => void;

  playbackRate: number;
  setPlaybackRate: (playbackRate: number) => void;

  normalize: boolean;
  toggleNormalize: () => void;

  setSource: (source: string) => void;
  clearSource: () => void;

  seek: (time: number) => void;
  play: (start?: number, end?: number) => void;
  pause: () => void;

  download: () => void;
};

type AudioContextProvider = {
  children: ReactNode;
};

export const AudioContext = createContext<AudioContext>({
  time: 0,
  state: 'pause',
  stopTime: undefined,
  source: undefined,
  duration: undefined,
  setStopTime: () => {
  },

  playbackRate: 1,
  setPlaybackRate: () => {
  },

  normalize: false,
  toggleNormalize: () => {
  },

  setSource: () => {
  },
  clearSource: () => {
  },

  seek: () => {
  },
  play: () => {
  },
  pause: () => {
  },
  download: () => {
  },

})

export const AudioProvider: React.FC<AudioContextProvider> = ({ children }) => {
  const elementRef = useRef<HTMLAudioElement | null>(null);
  const [ time, _setTime ] = useState<number>(0);
  const [ duration, _setDuration ] = useState<number | undefined>();
  const [ stopTime, _setStopTime ] = useState<number | undefined>();
  const stopTimeRef = useRef<number | undefined>();
  const [ playbackRate, _setPlaybackRate ] = useState<number>(1);
  const [ state, _setState ] = useState<AudioState>('pause');
  const [ source, setSource ] = useState<string | undefined>();
  const toast = useToast();

  // Web Audio API for normalization
  const webAudioCtxRef = useRef<globalThis.AudioContext | null>(null);
  const mediaSourceRef = useRef<MediaElementAudioSourceNode | null>(null);
  const gainNodeRef = useRef<GainNode | null>(null);
  const compressorRef = useRef<DynamicsCompressorNode | null>(null);
  const [ normalize, _setNormalize ] = useState(false);
  const normalizeRef = useRef(false);

  useEffect(() => {
    _setTime(0)
    pause()
    _setState('pause')
    _setStopTime(undefined)
    const interval = setInterval(() => {
      if (!elementRef.current || elementRef.current?.paused) return;

      const time = elementRef.current?.currentTime;
      if (stopTimeRef.current && time && time > stopTimeRef.current) pause();
      else _setTime(time)
    }, 1 / 30) // 1/30 is the more common video FPS os it should be enough to update currentTime in view

    return () => clearInterval(interval)
  }, [ source ]);

  const connectAudioGraph = useCallback((doNormalize: boolean) => {
    const ctx = webAudioCtxRef.current;
    const source = mediaSourceRef.current;
    const gain = gainNodeRef.current;
    const compressor = compressorRef.current;
    if (!ctx || !source || !gain || !compressor) return;

    source.disconnect();
    gain.disconnect();

    if (doNormalize) {
      // Boost quiet audio then compress to prevent clipping
      gain.gain.value = 4.0;
      source.connect(gain);
      gain.connect(compressor);
      compressor.connect(ctx.destination);
    } else {
      gain.gain.value = 1.0;
      source.connect(ctx.destination);
    }
  }, []);

  const initWebAudio = useCallback(() => {
    if (!elementRef.current || mediaSourceRef.current) return;
    try {
      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
      webAudioCtxRef.current = ctx;

      const source = ctx.createMediaElementSource(elementRef.current);
      mediaSourceRef.current = source;

      const gain = ctx.createGain();
      gainNodeRef.current = gain;

      const compressor = ctx.createDynamicsCompressor();
      compressor.threshold.value = -24;
      compressor.knee.value = 30;
      compressor.ratio.value = 12;
      compressor.attack.value = 0.003;
      compressor.release.value = 0.25;
      compressorRef.current = compressor;

      // Apply current normalize preference
      if (normalizeRef.current) {
        gain.gain.value = 4.0;
        source.connect(gain);
        gain.connect(compressor);
        compressor.connect(ctx.destination);
      } else {
        gain.gain.value = 1.0;
        source.connect(ctx.destination);
      }
    } catch (e) {
      console.warn('Web Audio API not available:', e);
    }
  }, []);

  const toggleNormalize = useCallback(() => {
    const next = !normalizeRef.current;
    normalizeRef.current = next;
    _setNormalize(next);
    connectAudioGraph(next);
  }, [ connectAudioGraph ]);

  const setStopTime = useCallback((stopTime?: number) => {
    _setStopTime(stopTime)
    stopTimeRef.current = stopTime;
  }, [ _setStopTime ])

  const setPlaybackRate = useCallback((playbackRate: number) => {
    _setPlaybackRate(playbackRate)
    if (elementRef.current) {
      elementRef.current.playbackRate = playbackRate;
      elementRef.current.preservesPitch = false;
    }
  }, [ _setPlaybackRate ])

  const seek = useCallback((time: number) => {
    if (!elementRef?.current) return;
    elementRef.current.currentTime = time;
    _setTime(time)
  }, [ _setTime ])

  const onLoad = useCallback(() => {
    _setTime(0)
    _setState('pause')
    if (elementRef.current) {
      elementRef.current.playbackRate = playbackRate;
      elementRef.current.preservesPitch = false;
      elementRef.current.volume = 1.0;
      _setDuration(elementRef.current.duration)
    }
  }, [ playbackRate, _setTime, _setState, _setDuration ])

  const play = useCallback((start?: number, end?: number) => {
    initWebAudio();
    if (webAudioCtxRef.current?.state === 'suspended') {
      webAudioCtxRef.current.resume();
    }
    if (start) seek(start)
    setStopTime(end)
    elementRef?.current?.play().catch(error => {
      toast.raiseError({
        message: 'Audio failed playing',
        error,
      })
    });
  }, [ seek, setStopTime, initWebAudio ])

  const onPlay = useCallback(() => {
    _setState('play')
  }, [ _setState ])

  const pause = useCallback(() => {
    elementRef?.current?.pause();
  }, [])

  const onPause = useCallback(() => {
    _setState('pause')
  }, [ _setState ])

  const download = useCallback(() => {
    if (!source) return;
    const link = document.createElement('a');
    link.href = source;
    link.target = '_blank';
    const pathSplit = source.split('/')
    link.download = pathSplit[pathSplit.length - 1];
    link.click();
  }, [ source ])

  const contextValue: AudioContext = useMemo(() => ({
    time, state, source, duration,
    stopTime, setStopTime,
    playbackRate, setPlaybackRate,
    normalize, toggleNormalize,
    setSource,
    clearSource: () => {
      setSource(undefined)
    },
    seek, play, pause, download,
  }), [ time, source, playbackRate, duration, setPlaybackRate, state, stopTime, setStopTime, normalize, toggleNormalize, setSource, pause, play, seek, download ]);

  return (
    <AudioContext.Provider value={ contextValue }>
      { children }

      <audio autoPlay={ false }
             controls={ false }
             loop={ false }
             muted={ false }
             ref={ elementRef }
             onLoadedMetadata={ onLoad }
             onPause={ onPause } onEnded={ onPause } onAbort={ onPause }
             onPlay={ onPlay }
             preload="auto"
             src={ source }
             title={ source }>
        <p>Your browser does not support the <code>audio</code> element.</p>
      </audio>
    </AudioContext.Provider>
  )
}

export const useAudio = () => {
  const context = useContext(AudioContext);
  if (!context) {
    throw new Error('useAudio must be used within a AudioProvider');
  }
  return context;
}
