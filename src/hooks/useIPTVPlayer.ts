import { useRef, useState, useCallback, useEffect } from 'react';
import Hls from 'hls.js';

export const useIPTVPlayer = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const hlsRef = useRef<Hls | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentUrl, setCurrentUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const destroyHls = useCallback(() => {
    if (hlsRef.current) {
      hlsRef.current.destroy();
      hlsRef.current = null;
    }
  }, []);

  const playStream = useCallback((url: string) => {
    if (!videoRef.current) return;
    
    destroyHls();
    setError(null);
    setCurrentUrl(url);

    const video = videoRef.current;

    if (url.includes('.m3u8')) {
      if (Hls.isSupported()) {
        const hls = new Hls({
          enableWorker: true,
          lowLatencyMode: true,
        });
        hlsRef.current = hls;
        
        hls.loadSource(url);
        hls.attachMedia(video);
        
        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          video.play().catch(e => console.log('Autoplay blocked:', e));
          setIsPlaying(true);
        });
        
        hls.on(Hls.Events.ERROR, (_, data) => {
          if (data.fatal) {
            setError('Erro ao carregar stream');
            setIsPlaying(false);
          }
        });
      } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = url;
        video.addEventListener('loadedmetadata', () => {
          video.play().catch(e => console.log('Autoplay blocked:', e));
          setIsPlaying(true);
        });
      }
    } else {
      video.src = url;
      video.addEventListener('loadedmetadata', () => {
        video.play().catch(e => console.log('Autoplay blocked:', e));
        setIsPlaying(true);
      });
    }
  }, [destroyHls]);

  const stop = useCallback(() => {
    destroyHls();
    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.src = '';
    }
    setIsPlaying(false);
    setCurrentUrl(null);
  }, [destroyHls]);

  useEffect(() => {
    return () => {
      destroyHls();
    };
  }, [destroyHls]);

  return {
    videoRef,
    isPlaying,
    currentUrl,
    error,
    playStream,
    stop,
  };
};
