import { forwardRef, useState } from 'react';
import { Maximize2, Volume2, VolumeX, Play, Pause } from 'lucide-react';
import { Channel } from '@/types/iptv';
import { cn } from '@/lib/utils';

interface VideoPlayerProps {
  channel: Channel | null;
  isPlaying: boolean;
}

export const VideoPlayer = forwardRef<HTMLVideoElement, VideoPlayerProps>(
  ({ channel, isPlaying }, ref) => {
    const [isMuted, setIsMuted] = useState(false);
    const [showControls, setShowControls] = useState(false);

    const handleFullscreen = () => {
      const video = (ref as React.RefObject<HTMLVideoElement>)?.current;
      if (video) {
        if (document.fullscreenElement) {
          document.exitFullscreen();
        } else {
          video.requestFullscreen();
        }
      }
    };

    const toggleMute = () => {
      const video = (ref as React.RefObject<HTMLVideoElement>)?.current;
      if (video) {
        video.muted = !video.muted;
        setIsMuted(!isMuted);
      }
    };

    return (
      <div 
        className="relative bg-black rounded-lg overflow-hidden aspect-video"
        onMouseEnter={() => setShowControls(true)}
        onMouseLeave={() => setShowControls(false)}
      >
        <video
          ref={ref}
          className="w-full h-full object-contain"
          controls={false}
          playsInline
        />

        {/* EPG Overlay */}
        {channel?.epg && (
          <div className="absolute top-4 left-4 right-4">
            <div className="bg-black/60 backdrop-blur-sm rounded-lg px-4 py-2 inline-block">
              <p className="text-xs text-muted-foreground uppercase tracking-wider">A SEGUIR</p>
              <p className="text-accent font-semibold text-sm">{channel.epg.next || 'CAÇADORES DE FUGITIVOS'}</p>
            </div>
          </div>
        )}

        {/* Channel Logo Overlay */}
        {channel && (
          <div className="absolute bottom-4 right-4">
            <div className="bg-black/40 backdrop-blur-sm rounded px-2 py-1">
              <span className="text-foreground text-xs font-medium">A&E</span>
            </div>
          </div>
        )}

        {/* Placeholder when no video */}
        {!channel && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-secondary to-background">
            <Play className="w-16 h-16 text-muted-foreground/50 mb-4" />
            <p className="text-muted-foreground text-sm">Selecione um canal para assistir</p>
          </div>
        )}

        {/* Controls Overlay */}
        <div 
          className={cn(
            'absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent transition-opacity',
            showControls ? 'opacity-100' : 'opacity-0'
          )}
        >
          <div className="flex items-center justify-end gap-2">
            <button
              onClick={toggleMute}
              className="w-8 h-8 rounded-full bg-foreground/20 flex items-center justify-center hover:bg-foreground/30 transition-colors"
            >
              {isMuted ? (
                <VolumeX className="w-4 h-4 text-foreground" />
              ) : (
                <Volume2 className="w-4 h-4 text-foreground" />
              )}
            </button>
            
            <button
              onClick={handleFullscreen}
              className="w-8 h-8 rounded-full bg-foreground/20 flex items-center justify-center hover:bg-foreground/30 transition-colors"
            >
              <Maximize2 className="w-4 h-4 text-foreground" />
            </button>
          </div>
        </div>
      </div>
    );
  }
);

VideoPlayer.displayName = 'VideoPlayer';
