import { useState, useCallback } from 'react';
import { Header } from './Header';
import { Navigation } from './Navigation';
import { ChannelList } from './ChannelList';
import { VideoPlayer } from './VideoPlayer';
import { SearchModal } from './SearchModal';
import { PlaylistModal } from './PlaylistModal';
import { useIPTVPlayer } from '@/hooks/useIPTVPlayer';
import { useIPTVData } from '@/hooks/useIPTVData';
import { Channel, NavTab } from '@/types/iptv';

export const IPTVPlayer = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('TV');
  const [selectedChannel, setSelectedChannel] = useState<Channel | null>(null);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isPlaylistOpen, setIsPlaylistOpen] = useState(false);

  const { videoRef, isPlaying, playStream } = useIPTVPlayer();
  const { 
    config, 
    saveConfig, 
    channels, 
    favorites, 
    toggleFavorite 
  } = useIPTVData();

  const handleChannelSelect = useCallback((channel: Channel) => {
    setSelectedChannel(channel);
    if (channel.url) {
      playStream(channel.url);
    }
  }, [playStream]);

  const handleTabChange = useCallback((tab: NavTab) => {
    setActiveTab(tab);
  }, []);

  return (
    <div className="h-screen flex flex-col bg-background overflow-hidden">
      {/* Header */}
      <Header 
        onSearchClick={() => setIsSearchOpen(true)}
        onProfileClick={() => setIsPlaylistOpen(true)}
      />

      {/* Navigation */}
      <Navigation activeTab={activeTab} onTabChange={handleTabChange} />

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Channel List Sidebar */}
        <div className="w-80 flex-shrink-0 border-r border-border bg-secondary/30 overflow-hidden">
          <ChannelList
            channels={channels}
            selectedChannel={selectedChannel}
            favorites={favorites}
            onChannelSelect={handleChannelSelect}
            onToggleFavorite={toggleFavorite}
          />
        </div>

        {/* Video Player */}
        <div className="flex-1 p-4 flex items-center justify-center">
          <div className="w-full max-w-4xl">
            <VideoPlayer
              ref={videoRef}
              channel={selectedChannel}
              isPlaying={isPlaying}
            />
          </div>
        </div>
      </div>

      {/* Modals */}
      <SearchModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        channels={channels}
        onChannelSelect={handleChannelSelect}
      />

      <PlaylistModal
        isOpen={isPlaylistOpen}
        onClose={() => setIsPlaylistOpen(false)}
        config={config}
        onSave={saveConfig}
      />
    </div>
  );
};
