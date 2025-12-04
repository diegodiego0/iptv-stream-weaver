import { cn } from '@/lib/utils';
import { NavTab } from '@/types/iptv';

interface NavigationProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
}

const tabs: { id: NavTab; label: string; special?: boolean }[] = [
  { id: 'TV', label: 'TV' },
  { id: 'JOGOS', label: 'JOGOS' },
  { id: 'DESTAQUES', label: 'DESTAQUES' },
  { id: 'FILMES', label: 'FILMES' },
  { id: 'SÉRIES', label: 'SÉRIES' },
  { id: 'KIDS', label: 'KIDS', special: true },
  { id: 'ANIME', label: 'ANIME' },
  { id: 'EXPLORAR', label: 'EXPLORAR' },
];

export const Navigation = ({ activeTab, onTabChange }: NavigationProps) => {
  return (
    <nav className="flex items-center gap-6 px-4 py-3 overflow-x-auto scrollbar-hide">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={cn(
            'text-sm font-semibold tracking-wide whitespace-nowrap transition-colors',
            activeTab === tab.id
              ? 'text-foreground'
              : 'text-muted-foreground hover:text-foreground',
            tab.special && 'text-iptv-kids font-bold'
          )}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
};
