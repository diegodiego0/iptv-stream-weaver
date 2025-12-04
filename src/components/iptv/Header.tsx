import { Search, Filter, Clock, User, Bell, Wifi } from 'lucide-react';
import { useState, useEffect } from 'react';

interface HeaderProps {
  onSearchClick: () => void;
  onProfileClick: () => void;
}

export const Header = ({ onSearchClick, onProfileClick }: HeaderProps) => {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <header className="flex items-center justify-between px-4 py-2 bg-secondary/50">
      {/* Logo */}
      <div className="flex items-center gap-2">
        <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
          <span className="text-primary font-bold text-lg">⊛</span>
        </div>
        <span className="text-foreground font-semibold text-lg tracking-wide">UniTV</span>
      </div>

      {/* Right Icons */}
      <div className="flex items-center gap-3">
        <button 
          onClick={onSearchClick}
          className="w-9 h-9 rounded-full bg-primary/80 flex items-center justify-center hover:bg-primary transition-colors"
        >
          <Search className="w-4 h-4 text-primary-foreground" />
        </button>
        
        <button className="w-9 h-9 rounded-full bg-primary/80 flex items-center justify-center hover:bg-primary transition-colors">
          <Filter className="w-4 h-4 text-primary-foreground" />
        </button>
        
        <button className="w-9 h-9 rounded-full bg-primary/80 flex items-center justify-center hover:bg-primary transition-colors">
          <Clock className="w-4 h-4 text-primary-foreground" />
        </button>
        
        <button 
          onClick={onProfileClick}
          className="w-9 h-9 rounded-full bg-primary/80 flex items-center justify-center hover:bg-primary transition-colors"
        >
          <User className="w-4 h-4 text-primary-foreground" />
        </button>
        
        <button className="w-9 h-9 rounded-full bg-primary/80 flex items-center justify-center hover:bg-primary transition-colors">
          <Bell className="w-4 h-4 text-primary-foreground" />
        </button>
        
        <div className="flex items-center gap-2 text-muted-foreground ml-2">
          <Wifi className="w-4 h-4" />
          <span className="text-sm font-medium">{formatTime(time)}</span>
        </div>
        
        <span className="text-sm text-muted-foreground ml-1">Perfil</span>
      </div>
    </header>
  );
};
