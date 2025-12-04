import { useState, useCallback, useEffect } from 'react';
import { Channel, Category, IPTVConfig } from '@/types/iptv';

// Sample data for demo
const sampleChannels: Channel[] = [
  { id: '1', name: 'A Fazenda 17 Sin..', logo: 'https://via.placeholder.com/60x60/8B0000/FFFFFF?text=AF', url: '', category: 'Entretenimento', epg: { current: 'A Fazenda 17', next: 'Caçadores de Fugitivos' } },
  { id: '2', name: 'A Fazenda 17 Sin..', logo: 'https://via.placeholder.com/60x60/8B0000/FFFFFF?text=AF', url: '', category: 'Entretenimento' },
  { id: '3', name: 'A Fazenda 17 Sin..', logo: 'https://via.placeholder.com/60x60/8B0000/FFFFFF?text=AF', url: '', category: 'Entretenimento' },
  { id: '4', name: 'A Fazenda 17 Sin..', logo: 'https://via.placeholder.com/60x60/8B0000/FFFFFF?text=AF', url: '', category: 'Entretenimento' },
  { id: '5', name: 'A Fazenda 17 Sin..', logo: 'https://via.placeholder.com/60x60/8B0000/FFFFFF?text=AF', url: '', category: 'Entretenimento' },
  { id: '6', name: 'A Fazenda 17 Sin..', logo: 'https://via.placeholder.com/60x60/8B0000/FFFFFF?text=AF', url: '', category: 'Entretenimento' },
  { id: '7', name: 'UFC Fight Pass', logo: 'https://via.placeholder.com/60x60/000000/FF0000?text=UFC', url: '', category: 'Esportes' },
];

const sampleCategories: Category[] = [
  { id: 'all', name: 'Todos' },
  { id: 'ent', name: 'Entretenimento' },
  { id: 'sports', name: 'Esportes' },
  { id: 'movies', name: 'Filmes' },
  { id: 'news', name: 'Notícias' },
];

export const useIPTVData = () => {
  const [config, setConfig] = useState<IPTVConfig>(() => {
    try {
      const saved = localStorage.getItem('iptv-config');
      return saved ? JSON.parse(saved) : { server: '', username: '', password: '' };
    } catch {
      return { server: '', username: '', password: '' };
    }
  });

  const [channels, setChannels] = useState<Channel[]>(sampleChannels);
  const [categories, setCategories] = useState<Category[]>(sampleCategories);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [favorites, setFavorites] = useState<Set<string>>(() => {
    try {
      const saved = localStorage.getItem('iptv-favorites');
      return saved ? new Set(JSON.parse(saved)) : new Set();
    } catch {
      return new Set();
    }
  });
  const [isLoading, setIsLoading] = useState(false);

  const saveConfig = useCallback((newConfig: IPTVConfig) => {
    setConfig(newConfig);
    localStorage.setItem('iptv-config', JSON.stringify(newConfig));
  }, []);

  const toggleFavorite = useCallback((id: string) => {
    setFavorites(prev => {
      const newFavorites = new Set(prev);
      if (newFavorites.has(id)) {
        newFavorites.delete(id);
      } else {
        newFavorites.add(id);
      }
      localStorage.setItem('iptv-favorites', JSON.stringify([...newFavorites]));
      return newFavorites;
    });
  }, []);

  const loadChannels = useCallback(async (categoryId?: string) => {
    if (!config.server) {
      setChannels(sampleChannels);
      return;
    }

    setIsLoading(true);
    try {
      const url = categoryId 
        ? `${config.server}/player_api.php?username=${config.username}&password=${config.password}&action=get_live_streams&category_id=${categoryId}`
        : `${config.server}/player_api.php?username=${config.username}&password=${config.password}&action=get_live_streams`;
      
      const response = await fetch(url);
      const data = await response.json();
      
      const mappedChannels: Channel[] = data.map((ch: any) => ({
        id: ch.stream_id?.toString() || ch.num?.toString(),
        name: ch.name,
        logo: ch.stream_icon,
        url: `${config.server}/live/${config.username}/${config.password}/${ch.stream_id}.m3u8`,
        category: ch.category_id,
      }));
      
      setChannels(mappedChannels);
    } catch (error) {
      console.error('Error loading channels:', error);
      setChannels(sampleChannels);
    } finally {
      setIsLoading(false);
    }
  }, [config]);

  const loadCategories = useCallback(async () => {
    if (!config.server) {
      setCategories(sampleCategories);
      return;
    }

    try {
      const response = await fetch(
        `${config.server}/player_api.php?username=${config.username}&password=${config.password}&action=get_live_categories`
      );
      const data = await response.json();
      
      const mappedCategories: Category[] = [
        { id: 'all', name: 'Todos' },
        ...data.map((cat: any) => ({
          id: cat.category_id,
          name: cat.category_name,
        })),
      ];
      
      setCategories(mappedCategories);
    } catch (error) {
      console.error('Error loading categories:', error);
      setCategories(sampleCategories);
    }
  }, [config]);

  useEffect(() => {
    loadCategories();
    loadChannels();
  }, [loadCategories, loadChannels]);

  const filteredChannels = selectedCategory === 'all' 
    ? channels 
    : channels.filter(ch => ch.category === selectedCategory);

  return {
    config,
    saveConfig,
    channels: filteredChannels,
    categories,
    selectedCategory,
    setSelectedCategory,
    favorites,
    toggleFavorite,
    isLoading,
    loadChannels,
  };
};
