import { Channel } from '@/types/iptv';
import { Heart } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChannelListProps {
  channels: Channel[];
  selectedChannel: Channel | null;
  favorites: Set<string>;
  onChannelSelect: (channel: Channel) => void;
  onToggleFavorite: (id: string) => void;
}

export const ChannelList = ({
  channels,
  selectedChannel,
  favorites,
  onChannelSelect,
  onToggleFavorite,
}: ChannelListProps) => {
  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-border">
        <h2 className="text-foreground font-medium text-sm">Lista de Canais</h2>
      </div>
      
      <div className="flex-1 overflow-y-auto">
        {channels.map((channel, index) => (
          <div
            key={channel.id}
            onClick={() => onChannelSelect(channel)}
            className={cn(
              'flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-all border-b border-border/50 animate-slide-in',
              selectedChannel?.id === channel.id
                ? 'bg-primary/20 border-l-4 border-l-primary'
                : 'hover:bg-secondary/80'
            )}
            style={{ animationDelay: `${index * 50}ms` }}
          >
            {/* Channel Logo */}
            <div className="w-12 h-12 rounded-lg overflow-hidden flex-shrink-0 bg-muted">
              {channel.logo ? (
                <img
                  src={channel.logo}
                  alt={channel.name}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = `https://via.placeholder.com/60x60/8B0000/FFFFFF?text=${channel.name.charAt(0)}`;
                  }}
                />
              ) : (
                <div className="w-full h-full bg-primary/30 flex items-center justify-center text-foreground font-bold">
                  {channel.name.charAt(0)}
                </div>
              )}
            </div>

            {/* Channel Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground text-sm">{index + 1}</span>
                <span className="text-foreground text-sm font-medium truncate">
                  {channel.name}
                </span>
              </div>
            </div>

            {/* Favorite Button */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggleFavorite(channel.id);
              }}
              className="p-1.5 rounded-full hover:bg-muted transition-colors"
            >
              <Heart
                className={cn(
                  'w-4 h-4 transition-colors',
                  favorites.has(channel.id)
                    ? 'fill-primary text-primary'
                    : 'text-muted-foreground'
                )}
              />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
