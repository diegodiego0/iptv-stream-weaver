import { useState } from 'react';
import { Search, X } from 'lucide-react';
import { Channel } from '@/types/iptv';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  channels: Channel[];
  onChannelSelect: (channel: Channel) => void;
}

export const SearchModal = ({ isOpen, onClose, channels, onChannelSelect }: SearchModalProps) => {
  const [query, setQuery] = useState('');

  const filteredChannels = query.length > 0
    ? channels.filter(ch => 
        ch.name.toLowerCase().includes(query.toLowerCase())
      )
    : [];

  const handleSelect = (channel: Channel) => {
    onChannelSelect(channel);
    onClose();
    setQuery('');
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-card border-border max-w-md">
        <DialogHeader>
          <DialogTitle className="text-foreground flex items-center gap-2">
            <Search className="w-5 h-5" />
            Buscar Canal
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Digite o nome do canal..."
              className="pl-10 bg-secondary border-border text-foreground placeholder:text-muted-foreground"
              autoFocus
            />
            {query && (
              <button
                onClick={() => setQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2"
              >
                <X className="w-4 h-4 text-muted-foreground hover:text-foreground" />
              </button>
            )}
          </div>

          <div className="max-h-64 overflow-y-auto space-y-1">
            {filteredChannels.map((channel) => (
              <button
                key={channel.id}
                onClick={() => handleSelect(channel)}
                className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-secondary transition-colors text-left"
              >
                <div className="w-10 h-10 rounded-lg overflow-hidden bg-muted flex-shrink-0">
                  {channel.logo ? (
                    <img
                      src={channel.logo}
                      alt={channel.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full bg-primary/30 flex items-center justify-center text-foreground font-bold">
                      {channel.name.charAt(0)}
                    </div>
                  )}
                </div>
                <span className="text-foreground text-sm">{channel.name}</span>
              </button>
            ))}
            
            {query && filteredChannels.length === 0 && (
              <p className="text-center text-muted-foreground py-8">
                Nenhum canal encontrado
              </p>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
