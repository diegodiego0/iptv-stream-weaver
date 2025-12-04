export interface Channel {
  id: string;
  name: string;
  logo?: string;
  url: string;
  category?: string;
  epg?: EPGInfo;
}

export interface EPGInfo {
  current?: string;
  next?: string;
  progress?: number;
}

export interface Movie {
  id: string;
  name: string;
  poster?: string;
  url: string;
  year?: string;
  rating?: number;
  category?: string;
}

export interface Series {
  id: string;
  name: string;
  poster?: string;
  year?: string;
  rating?: number;
  category?: string;
}

export interface Episode {
  id: string;
  season: number;
  episode_num: number;
  title: string;
  url: string;
  duration?: string;
}

export interface Radio {
  id: string;
  name: string;
  logo?: string;
  url: string;
  category?: string;
}

export interface Category {
  id: string;
  name: string;
}

export interface IPTVConfig {
  server: string;
  username: string;
  password: string;
}

export type ContentType = 'channels' | 'movies' | 'series' | 'radios' | 'favorites';
export type NavTab = 'TV' | 'JOGOS' | 'DESTAQUES' | 'FILMES' | 'SÉRIES' | 'KIDS' | 'ANIME' | 'EXPLORAR';
