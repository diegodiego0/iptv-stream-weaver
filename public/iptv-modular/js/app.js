/**
 * =============================================
 * IPTV Player v1.1.3 - Lógica Principal
 * =============================================
 * EXTRAÍDO DO ARQUIVO HTML ORIGINAL
 * Mantém 100% da funcionalidade original
 * 
 * IMPORTANTE: Nenhuma função foi removida ou renomeada
 * Todos os IDs, classes e seletores originais mantidos
 * =============================================
 */

/* ========================================
   SISTEMA DE PROXY COM ROTAÇÃO DE IPs
   ======================================== */

// ATIVAR PROXY: Mude para true para usar proxy
const USE_PROXY = false;

// COLOQUE AQUI O LINK RAW DO GITHUB COM A LISTA DE IPs PROXY
const PROXY_LIST_URL = '';

// Lista de IPs proxy carregados
let proxyList = [];
let currentProxyIndex = 0;

// Carrega lista de proxies do GitHub
async function loadProxyList() {
  if (!USE_PROXY || !PROXY_LIST_URL) return;
  
  try {
    const response = await fetch(PROXY_LIST_URL);
    if (response.ok) {
      const text = await response.text();
      proxyList = text.split('\n')
        .map(line => line.trim())
        .filter(line => line && !line.startsWith('#'));
    }
  } catch (e) {
    // Silencioso - sem mensagens de erro
  }
}

// Obtém próximo proxy da lista (rotação automática)
function getNextProxy() {
  if (proxyList.length === 0) return null;
  const proxy = proxyList[currentProxyIndex];
  currentProxyIndex = (currentProxyIndex + 1) % proxyList.length;
  return proxy;
}

// Aplica proxy à URL do stream
function applyProxyToUrl(originalUrl) {
  if (!USE_PROXY || proxyList.length === 0) return originalUrl;
  
  const proxy = getNextProxy();
  if (!proxy) return originalUrl;
  
  return originalUrl;
}

// Tenta reconectar usando próximo proxy em caso de falha
function handleProxyFailure(originalUrl, callback) {
  if (!USE_PROXY || proxyList.length === 0) return;
  
  const newUrl = applyProxyToUrl(originalUrl);
  if (callback) callback(newUrl);
}

// Inicializa sistema de proxy
loadProxyList();

/* ========================================
   THEME FUNCTIONS
   ======================================== */

function openThemeModal() {
  document.getElementById('themeModal').style.display = 'flex';
  updateActiveTheme();
}

function closeThemeModal() {
  document.getElementById('themeModal').style.display = 'none';
}

function changeTheme(theme) {
  document.body.setAttribute('data-theme', theme);
  
  // Usa StorageCompat se disponível
  if (typeof StorageCompat !== 'undefined') {
    StorageCompat.setItem('iptv-theme', theme);
  } else {
    localStorage.setItem('iptv-theme', theme);
  }
  
  updateActiveTheme();
}

function updateActiveTheme() {
  const currentTheme = document.body.getAttribute('data-theme') || 'verde';
  document.querySelectorAll('.theme-option').forEach(option => {
    option.classList.remove('active');
    if (option.dataset.theme === currentTheme) {
      option.classList.add('active');
    }
  });
}

function loadTheme() {
  let savedTheme;
  
  if (typeof StorageCompat !== 'undefined') {
    savedTheme = StorageCompat.getItem('iptv-theme') || 'verde';
  } else {
    savedTheme = localStorage.getItem('iptv-theme') || 'verde';
  }
  
  document.body.setAttribute('data-theme', savedTheme);
}

// Função para carregar background personalizado da página
function loadPageBackground() {
  // URL do background - configure aqui ou deixe vazio para não usar
  const backgroundUrl = ' https://i.ibb.co/ksrcR8nC/bk.jpg ';
  
  if (backgroundUrl && backgroundUrl.trim() !== '') {
    document.body.style.setProperty('--page-background', `url('${backgroundUrl}')`);
    document.body.classList.add('has-background');
  } else {
    document.body.classList.remove('has-background');
  }
}

/* ========================================
   FAVORITES BACKEND CLASS
   ======================================== */

class FavoritesBackend {
  constructor() {
    this.favorites = new Map();
    this.syncInterval = null;
    this.lastSync = 0;
    this.loadFromStorage();
    this.startAutoSync();
  }

  loadFromStorage() {
    try {
      let saved;
      if (typeof StorageCompat !== 'undefined') {
        saved = StorageCompat.getItem('iptv-favorites-v2');
      } else {
        saved = localStorage.getItem('iptv-favorites-v2');
      }
      
      if (saved) {
        const data = JSON.parse(saved);
        this.favorites = new Map(data.favorites || []);
        this.lastSync = data.lastSync || 0;
      }
    } catch (error) {
      console.error('Erro ao carregar favoritos:', error);
    }
  }

  saveToStorage() {
    try {
      const data = {
        favorites: Array.from(this.favorites.entries()),
        lastSync: Date.now()
      };
      
      if (typeof StorageCompat !== 'undefined') {
        StorageCompat.setItem('iptv-favorites-v2', JSON.stringify(data));
      } else {
        localStorage.setItem('iptv-favorites-v2', JSON.stringify(data));
      }
    } catch (error) {
      console.error('Erro ao salvar favoritos:', error);
    }
  }

  startAutoSync() {
    this.syncInterval = setInterval(() => {
      this.saveToStorage();
    }, 10000);
  }

  addFavorite(id, item) {
    this.favorites.set(id, {
      ...item,
      favoriteDate: Date.now(),
      lastAccessed: Date.now()
    });
    this.saveToStorage();
    return true;
  }

  removeFavorite(id) {
    const removed = this.favorites.delete(id);
    if (removed) {
      this.saveToStorage();
    }
    return removed;
  }

  isFavorite(id) {
    return this.favorites.has(id);
  }

  getFavorites() {
    return Array.from(this.favorites.values())
      .sort((a, b) => b.lastAccessed - a.lastAccessed);
  }

  updateLastAccessed(id) {
    if (this.favorites.has(id)) {
      const item = this.favorites.get(id);
      item.lastAccessed = Date.now();
      this.favorites.set(id, item);
      this.saveToStorage();
    }
  }

  getFavoritesByType(type) {
    return this.getFavorites().filter(item => item.type === type);
  }

  clearAll() {
    this.favorites.clear();
    this.saveToStorage();
  }
}

/* ========================================
   IPTV APP CLASS
   ======================================== */

class IPTVApp {
  constructor() {
    this.categories = [];
    this.movieCategories = [];
    this.seriesCategories = [];
    this.channels = [];
    this.movies = [];
    this.series = [];
    this.radios = [];
    this.episodes = [];
    this.allContent = [];
    this.favorites = new Set();
    this.favoritesBackend = new FavoritesBackend();
    this.favoritesList = new Map();
    this.watchProgress = new Map();
    this.currentChannel = null;
    this.currentMovie = null;
    this.currentSeries = null;
    this.currentEpisode = null;
    this.currentRadio = null;
    this.currentEpisodeIndex = 0;
    this.activeCategory = null;
    this.activeMovieCategory = null;
    this.activeSeriesCategory = null;
    this.activeRadioCategory = 'all';
    this.activeContent = 'channels';
    this.player = null;
    this.hls = null;
    this.progressSaveInterval = null;
    this.cache = new Map();
    this.cacheExpiration = 30 * 60 * 1000;
    this.retryAttempts = 3;
    this.retryDelay = 1000;
    this.favoritesBackend = new FavoritesBackend();
    this.favoritesList = new Map();
    
    this.radioVideoMode = false;
    
    this.epgCache = new Map();
    this.epgCacheExpiration = 5 * 60 * 1000;
    
    this.config = {
      server: 'http://c.maintech.top',
      githubRawUrl: 'https://raw.githubusercontent.com/1IPTVPLAYERv/radios/refs/heads/main/radios.json ',
      username: 'IPTVBR',
      password: 'IPTVBR'
    };
    this.initRadios();
    this.init();
  }

  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  async initRadios() {
    this.radios = [];
    await this.loadRadiosFromGitHubRaw();
  }
  
  async loadRadiosFromGitHubRaw() {
    const githubRawUrl = this.config.githubRawUrl || '';
    
    if (!githubRawUrl) {
      console.log('URL do GitHub RAW não configurada');
      return;
    }
    
    try {
      console.log('Carregando rádios extras do GitHub RAW:', githubRawUrl);
      const response = await fetch(githubRawUrl);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.text();
      
      let extraRadios;
      try {
        extraRadios = JSON.parse(data);
      } catch (parseError) {
        console.error('Erro ao fazer parse do JSON:', parseError);
        return;
      }
      
      if (!Array.isArray(extraRadios)) {
        console.error('O arquivo RAW deve conter um array de rádios');
        return;
      }
      
      console.log(`Adicionando ${extraRadios.length} rádios extras`);
      this.radios = [...this.radios, ...extraRadios];
      
    } catch (error) {
      console.error('Erro ao carregar rádios do GitHub RAW:', error);
    }
  }

  async init() {
    try {
      this.loadConfig();
      this.loadFavorites();
      this.loadWatchProgress();
      this.initPlayer();
      this.setupEventListeners();
      
      await Promise.all([
        this.loadCategories(),
        this.loadMovieCategories(),
        this.loadSeriesCategories()
      ]);
      
      this.renderRadios();
      this.loadGames();
    } catch (error) {
      console.error('Erro ao inicializar app:', error);
      this.showErrorOverlay('Erro ao inicializar aplicativo', () => this.init());
    }
  }

  initPlayer() {
    this.player = videojs('videoPlayer', {
      fluid: true,
      responsive: true,
      controls: true,
      preload: 'auto',
      html5: {
        hls: {
          enableLowInitialPlaylist: true,
          smoothQualityChange: true,
          overrideNative: !videojs.browser.IS_SAFARI
        }
      },
      audioQuality: 'high',
      techOrder: ['html5'],
      sources: [],
      playbackRates: [0.5, 1, 1.25, 1.5, 2]
    });

    this.player.on('timeupdate', () => {
      this.saveWatchProgress();
    });

    this.player.on('ended', () => {
      if (this.currentEpisode && this.currentEpisodeIndex < this.episodes.length - 1) {
        this.playNextEpisode();
      }
    });

    this.player.on('error', () => {
      console.error('Erro no player:', this.player.error());
      this.showErrorOverlay('Erro no reprodutor', () => {
        if (this.currentChannel) this.playChannel({id: this.currentChannel});
        else if (this.currentMovie) this.playMovie(this.currentMovie);
        else if (this.currentEpisode) this.playEpisode(this.currentEpisode, this.currentEpisodeIndex);
        else if (this.currentRadio) this.playRadio(this.currentRadio);
      });
    });
  }

  setupAdvancedPlayer(url, type) {
    const video = this.player.el().querySelector('video');
    
    if (this.hls) {
      this.hls.destroy();
      this.hls = null;
    }

    video.src = '';
    video.load();

    const extension = url.split('.').pop().toLowerCase().split('?')[0];
    const isHLS = extension === 'm3u8' || extension === 'm3u' || extension === 'ts' || url.includes('m3u8');
    
    if (isHLS && Hls.isSupported()) {
      console.log('Usando HLS.js para stream:', url);
      this.hls = new Hls({
        enableWorker: true,
        lowLatencyMode: type === 'channel' || type === 'radio-video',
        backBufferLength: type === 'channel' ? 30 : 90,
        maxBufferLength: type === 'channel' ? 15 : 30,
        maxMaxBufferLength: type === 'channel' ? 300 : 600,
        maxBufferSize: 60 * 1000 * 1000,
        maxBufferHole: 0.5,
        nudgeOffset: 0.1,
        nudgeMaxRetry: 3,
        maxFragLookUpTolerance: 0.25,
        liveSyncDurationCount: 3,
        manifestLoadingTimeOut: 10000,
        fragLoadingTimeOut: 20000
      });
      
      this.hls.loadSource(url);
      this.hls.attachMedia(video);
      
      this.hls.on(Hls.Events.MANIFEST_PARSED, () => {
        console.log('HLS manifest carregado com sucesso');
      });
      
      this.hls.on(Hls.Events.ERROR, (event, data) => {
        console.error('HLS Error:', data.type, data.details, data);
        if (data.fatal) {
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              console.log('Erro de rede HLS - URL pode estar bloqueada (CORS/HTTPS):', url);
              console.log('Tentando recuperar...');
              this.hls.startLoad();
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              console.log('Erro de mídia HLS, tentando recuperar...');
              this.hls.recoverMediaError();
              break;
            default:
              console.log('Erro fatal HLS, destruindo instância...');
              this.hls.destroy();
              break;
          }
        }
      });
    } else if (isHLS && !Hls.isSupported() && video.canPlayType('application/vnd.apple.mpegurl')) {
      console.log('Usando HLS nativo (Safari):', url);
      video.src = url;
    } else {
      let mimeType = 'video/mp4';
      
      if (type === 'radio' && (extension === 'mp3' || extension === 'aac' || extension === 'ogg')) {
        mimeType = 'audio/mpeg';
      } else if (type === 'radio-video') {
        if (extension === 'mp4') {
          mimeType = 'video/mp4';
        } else if (extension === 'webm') {
          mimeType = 'video/webm';
        } else if (extension === 'ogv') {
          mimeType = 'video/ogg';
        } else if (extension === 'm3u8' || extension === 'm3u') {
          mimeType = 'application/x-mpegURL';
        } else if (extension === 'ts') {
          mimeType = 'video/mp2t';
        }
      }
      
      console.log('Usando player nativo para formato:', extension, 'MIME:', mimeType);
      this.player.src({ type: mimeType, src: url });
    }
  }

  setupEventListeners() {
    // Theme button
    document.getElementById('themeBtn').addEventListener('click', openThemeModal);
    
    // Share button
    document.getElementById('shareBtn').addEventListener('click', () => this.shareApp());
    
    // Search button
    document.getElementById('searchBtn').addEventListener('click', () => {
      new bootstrap.Modal(document.getElementById('searchModal')).show();
    });
    
    // Add playlist button
    document.getElementById('addPlaylistBtn').addEventListener('click', () => {
      new bootstrap.Modal(document.getElementById('playlistModal')).show();
    });
    
    // Search input
    document.getElementById('searchInput').addEventListener('input', (e) => {
      this.performSearch(e.target.value);
    });
    
    // Save playlist button
    document.getElementById('savePlaylist').addEventListener('click', () => this.savePlaylist());
    
    // Main navigation
    document.querySelectorAll('.main-nav .nav-link').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const content = link.dataset.content;
        
        document.querySelectorAll('.main-nav .nav-link').forEach(l => l.classList.remove('active'));
        link.classList.add('active');
        
        this.showContentSection(content);
      });
    });
    
    // Error overlay buttons
    document.getElementById('retryBtn').addEventListener('click', () => {
      document.getElementById('errorOverlay').style.display = 'none';
      if (this.pendingRetryAction) {
        this.pendingRetryAction();
      }
    });
    
    document.getElementById('closeErrorBtn').addEventListener('click', () => {
      document.getElementById('errorOverlay').style.display = 'none';
    });
    
    // Continue watching modal
    document.getElementById('continueYes').addEventListener('click', () => {
      document.getElementById('continueModal').style.display = 'none';
      if (this.pendingContinueAction) {
        this.pendingContinueAction.continue();
      }
    });
    
    document.getElementById('continueNo').addEventListener('click', () => {
      document.getElementById('continueModal').style.display = 'none';
      if (this.pendingContinueAction) {
        this.pendingContinueAction.restart();
      }
    });
    
    // Episode navigation
    document.getElementById('prevEpisodeBtn').addEventListener('click', () => this.playPreviousEpisode());
    document.getElementById('nextEpisodeBtn').addEventListener('click', () => this.playNextEpisode());
    document.getElementById('episodeListBtn').addEventListener('click', () => this.toggleEpisodeNavigation());
    document.getElementById('episodeNavClose').addEventListener('click', () => this.hideEpisodeNavigation());
  }

  showContentSection(content) {
    this.activeContent = content;
    
    document.querySelectorAll('.content-section').forEach(section => {
      section.classList.remove('active');
      section.style.display = 'none';
    });
    
    const targetSection = document.getElementById(`${content}Section`);
    if (targetSection) {
      targetSection.classList.add('active');
      targetSection.style.display = 'block';
    }
    
    if (content === 'favorites') {
      this.renderFavorites();
    }
  }

  loadConfig() {
    try {
      let saved;
      if (typeof StorageCompat !== 'undefined') {
        saved = StorageCompat.getItem('iptv-config');
      } else {
        saved = localStorage.getItem('iptv-config');
      }
      
      if (saved) {
        this.config = JSON.parse(saved);
      }
    } catch (error) {
      console.error('Erro ao carregar configuração:', error);
    }
  }

  saveConfig() {
    try {
      if (typeof StorageCompat !== 'undefined') {
        StorageCompat.setItem('iptv-config', JSON.stringify(this.config));
      } else {
        localStorage.setItem('iptv-config', JSON.stringify(this.config));
      }
    } catch (error) {
      console.error('Erro ao salvar configuração:', error);
    }
  }

  getCachedData(key) {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheExpiration) {
      return cached.data;
    }
    return null;
  }

  setCachedData(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  async retryRequest(requestFn, attempts = this.retryAttempts) {
    for (let i = 0; i < attempts; i++) {
      try {
        return await requestFn();
      } catch (error) {
        if (i === attempts - 1) throw error;
        await new Promise(resolve => setTimeout(resolve, this.retryDelay * (i + 1)));
      }
    }
  }

  async loadCategories() {
    const cacheKey = 'categories';
    let categories = this.getCachedData(cacheKey);
    
    if (!categories) {
      try {
        categories = await this.retryRequest(async () => {
          const response = await fetch(`${this.config.server}/player_api.php?username=${this.config.username}&password=${this.config.password}&action=get_live_categories`);
          if (!response.ok) throw new Error('Erro na requisição');
          return response.json();
        });
        this.setCachedData(cacheKey, categories);
      } catch (error) {
        console.error('Erro ao carregar categorias:', error);
        this.showErrorOverlay('Erro ao carregar categorias', () => this.loadCategories());
        return;
      }
    }
    
    this.categories = categories;
    this.renderCategories();
    
    if (categories.length > 0) {
      this.activeCategory = categories[0].category_id;
      await this.loadChannels(this.activeCategory);
    }
  }

  async loadMovieCategories() {
    const cacheKey = 'movieCategories';
    let categories = this.getCachedData(cacheKey);
    
    if (!categories) {
      try {
        categories = await this.retryRequest(async () => {
          const response = await fetch(`${this.config.server}/player_api.php?username=${this.config.username}&password=${this.config.password}&action=get_vod_categories`);
          if (!response.ok) throw new Error('Erro na requisição');
          return response.json();
        });
        this.setCachedData(cacheKey, categories);
      } catch (error) {
        console.error('Erro ao carregar categorias de filmes:', error);
        return;
      }
    }
    
    this.movieCategories = categories;
    this.renderMovieCategories();
    
    if (categories.length > 0) {
      this.activeMovieCategory = categories[0].category_id;
      await this.loadMovies(this.activeMovieCategory);
    }
  }

  async loadSeriesCategories() {
    const cacheKey = 'seriesCategories';
    let categories = this.getCachedData(cacheKey);
    
    if (!categories) {
      try {
        categories = await this.retryRequest(async () => {
          const response = await fetch(`${this.config.server}/player_api.php?username=${this.config.username}&password=${this.config.password}&action=get_series_categories`);
          if (!response.ok) throw new Error('Erro na requisição');
          return response.json();
        });
        this.setCachedData(cacheKey, categories);
      } catch (error) {
        console.error('Erro ao carregar categorias de séries:', error);
        return;
      }
    }
    
    this.seriesCategories = categories;
    this.renderSeriesCategories();
    
    if (categories.length > 0) {
      this.activeSeriesCategory = categories[0].category_id;
      await this.loadSeries(this.activeSeriesCategory);
    }
  }

  renderCategories() {
    const tabNav = document.getElementById('channelTabs');
    tabNav.innerHTML = '';
    
    this.categories.forEach(category => {
      const btn = document.createElement('button');
      btn.className = 'tab-btn';
      btn.textContent = category.category_name;
      btn.dataset.categoryId = category.category_id;
      
      if (category.category_id === this.activeCategory) {
        btn.classList.add('active');
      }
      
      btn.addEventListener('click', () => {
        document.querySelectorAll('#channelTabs .tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.activeCategory = category.category_id;
        this.loadChannels(category.category_id);
      });
      
      tabNav.appendChild(btn);
    });
  }

  renderMovieCategories() {
    const tabNav = document.getElementById('movieTabs');
    tabNav.innerHTML = '';
    
    this.movieCategories.forEach(category => {
      const btn = document.createElement('button');
      btn.className = 'tab-btn';
      btn.textContent = category.category_name;
      btn.dataset.categoryId = category.category_id;
      
      if (category.category_id === this.activeMovieCategory) {
        btn.classList.add('active');
      }
      
      btn.addEventListener('click', () => {
        document.querySelectorAll('#movieTabs .tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.activeMovieCategory = category.category_id;
        this.loadMovies(category.category_id);
      });
      
      tabNav.appendChild(btn);
    });
  }

  renderSeriesCategories() {
    const tabNav = document.getElementById('seriesTabs');
    tabNav.innerHTML = '';
    
    this.seriesCategories.forEach(category => {
      const btn = document.createElement('button');
      btn.className = 'tab-btn';
      btn.textContent = category.category_name;
      btn.dataset.categoryId = category.category_id;
      
      if (category.category_id === this.activeSeriesCategory) {
        btn.classList.add('active');
      }
      
      btn.addEventListener('click', () => {
        document.querySelectorAll('#seriesTabs .tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.activeSeriesCategory = category.category_id;
        this.loadSeries(category.category_id);
      });
      
      tabNav.appendChild(btn);
    });
  }

  async loadChannels(categoryId) {
    const cacheKey = `channels-${categoryId}`;
    let channels = this.getCachedData(cacheKey);
    
    if (!channels) {
      try {
        channels = await this.retryRequest(async () => {
          const response = await fetch(`${this.config.server}/player_api.php?username=${this.config.username}&password=${this.config.password}&action=get_live_streams&category_id=${categoryId}`);
          if (!response.ok) throw new Error('Erro na requisição');
          const data = await response.json();
          return data.map(channel => ({
            id: channel.stream_id,
            name: channel.name,
            type: 'channel',
            icon: channel.stream_icon,
            epg_channel_id: channel.epg_channel_id,
            letter: channel.name.charAt(0).toUpperCase()
          }));
        });
        this.setCachedData(cacheKey, channels);
      } catch (error) {
        console.error('Erro ao carregar canais:', error);
        this.showErrorOverlay('Erro ao carregar canais', () => this.loadChannels(categoryId));
        return;
      }
    }
    
    this.channels = channels;
    this.allContent = this.allContent.filter(item => item.type !== 'channel');
    this.allContent.push(...this.channels);
    this.renderChannels();
  }

  async loadMovies(categoryId) {
    const cacheKey = `movies-${categoryId}`;
    let movies = this.getCachedData(cacheKey);
    
    if (!movies) {
      try {
        movies = await this.retryRequest(async () => {
          const response = await fetch(`${this.config.server}/player_api.php?username=${this.config.username}&password=${this.config.password}&action=get_vod_streams&category_id=${categoryId}`);
          if (!response.ok) throw new Error('Erro na requisição');
          const data = await response.json();
          return data.map(movie => ({
            id: movie.stream_id,
            name: movie.name || movie.title,
            type: 'movie',
            title: movie.title,
            year: movie.year,
            rating: movie.rating,
            icon: movie.stream_icon,
            plot: movie.plot,
            letter: (movie.name || movie.title).charAt(0).toUpperCase(),
            container_extension: movie.container_extension
          }));
        });
        this.setCachedData(cacheKey, movies);
      } catch (error) {
        console.error('Erro ao carregar filmes:', error);
        this.showErrorOverlay('Erro ao carregar filmes', () => this.loadMovies(categoryId));
        return;
      }
    }
    
    this.movies = movies;
    this.allContent = this.allContent.filter(item => item.type !== 'movie');
    this.allContent.push(...this.movies);
    this.renderMovies();
  }

  async loadSeries(categoryId) {
    const cacheKey = `series-${categoryId}`;
    let series = this.getCachedData(cacheKey);
    
    if (!series) {
      try {
        series = await this.retryRequest(async () => {
          const response = await fetch(`${this.config.server}/player_api.php?username=${this.config.username}&password=${this.config.password}&action=get_series&category_id=${categoryId}`);
          if (!response.ok) throw new Error('Erro na requisição');
          const data = await response.json();
          return data.map(series => ({
            id: series.series_id,
            name: series.name || series.title,
            type: 'series',
            title: series.title,
            year: series.year,
            rating: series.rating,
            icon: series.cover,
            plot: series.plot,
            letter: (series.name || series.title).charAt(0).toUpperCase()
          }));
        });
        this.setCachedData(cacheKey, series);
      } catch (error) {
        console.error('Erro ao carregar séries:', error);
        this.showErrorOverlay('Erro ao carregar séries', () => this.loadSeries(categoryId));
        return;
      }
    }
    
    this.series = series;
    this.allContent = this.allContent.filter(item => item.type !== 'series');
    this.allContent.push(...this.series);
    this.renderSeries();
  }

  renderChannels() {
    const channelList = document.getElementById('channelList');
    
    if (this.channels.length === 0) {
      channelList.innerHTML = `
        <div class="text-center p-4">
          <i class="fas fa-tv fa-3x text-muted mb-3"></i>
          <p class="text-muted">Nenhum canal encontrado nesta categoria</p>
        </div>
      `;
      return;
    }

    channelList.innerHTML = '';
    this.channels.forEach(channel => {
      const item = this.createContentItem(channel, 'channel');
      channelList.appendChild(item);
    });
  }

  renderMovies() {
    const movieList = document.getElementById('movieList');
    
    if (this.movies.length === 0) {
      movieList.innerHTML = `
        <div class="text-center p-4">
          <i class="fas fa-film fa-3x text-muted mb-3"></i>
          <p class="text-muted">Nenhum filme encontrado nesta categoria</p>
        </div>
      `;
      return;
    }

    movieList.innerHTML = '';
    this.movies.forEach(movie => {
      const item = this.createContentItem(movie, 'movie');
      movieList.appendChild(item);
    });
  }

  renderSeries() {
    const seriesList = document.getElementById('seriesList');
    
    if (this.series.length === 0) {
      seriesList.innerHTML = `
        <div class="text-center p-4">
          <i class="fas fa-play fa-3x text-muted mb-3"></i>
          <p class="text-muted">Nenhuma série encontrada nesta categoria</p>
        </div>
      `;
      return;
    }

    seriesList.innerHTML = '';
    this.series.forEach(series => {
      const item = this.createContentItem(series, 'series');
      seriesList.appendChild(item);
    });
  }

  renderRadios() {
    const radioList = document.getElementById('radioList');
    let filteredRadios = this.radios;
    
    if (this.activeRadioCategory !== 'all') {
      filteredRadios = this.radios.filter(radio => radio.category === this.activeRadioCategory);
    }

    if (filteredRadios.length === 0) {
      radioList.innerHTML = `
        <div class="text-center p-4">
          <i class="fas fa-radio fa-3x text-muted mb-3"></i>
          <p class="text-muted">Nenhuma rádio encontrada nesta categoria</p>
        </div>
      `;
      return;
    }

    radioList.innerHTML = '';
    filteredRadios.forEach(radio => {
      const item = this.createContentItem(radio, 'radio');
      radioList.appendChild(item);
    });
  }

  createContentItem(content, type) {
    const item = document.createElement('div');
    item.className = 'content-item';
    
    const isPlaying = (type === 'channel' && this.currentChannel === content.id) ||
                     (type === 'movie' && this.currentMovie?.id === content.id) ||
                     (type === 'series' && this.currentSeries?.id === content.id) ||
                     (type === 'radio' && this.currentRadio?.id === content.id);

    if (isPlaying) {
      item.classList.add('playing');
    }

    const avatarStyle = content.icon ? `background-image: url('${content.icon}'); background-size: cover; background-position: center;` : '';

    const progressKey = type === 'channel' ? `channel_${content.id}` : 
                       type === 'movie' ? `movie_${content.id}` : 
                       type === 'series' ? `series_${content.id}` :
                       `radio_${content.id}`;
    const progress = this.watchProgress.get(progressKey);
    let progressIndicator = '';

    let details = '';
    if (type === 'channel') {
      details = isPlaying ? '' : 'Toque para assistir';
    } else if (type === 'movie') {
      details = content.year ? `Ano: ${content.year}` : 'Filme';
    } else if (type === 'series') {
      details = 'Série';
    } else if (type === 'radio') {
      details = content.frequency || 'Rádio';
      if (content.city) details += ` • ${content.city}`;
      
      const hasVideo = content.video && content.video.trim() !== '' && content.video !== 'url_vídeo';
      if (hasVideo) {
        details += ' • 📺';
      }
      
      if (isPlaying) details = 'Tocando agora';
    }

    const epgLineSection = (type === 'channel' && isPlaying) ? `
      <div class="epg-line" data-epg-line-id="${content.id}">
        <i class="fas fa-spinner epg-line-loading"></i>
        <span class="epg-line-loading">Carregando EPG...</span>
      </div>
    ` : '';

    item.innerHTML = `
      <div class="content-avatar" style="${avatarStyle}">
        ${!content.icon ? content.letter : ''}
      </div>
      <div class="content-info">
        <div class="content-name-wrapper">
          <div class="content-name" data-name="${this.escapeHtml(content.name)}">${content.name}</div>
        </div>
        <div class="content-details">
          ${details}
          ${content.rating ? ` • ⭐ ${content.rating}` : ''}
          ${progressIndicator}
        </div>
      </div>
      ${isPlaying ? '<div class="playingindicator"></div>' : ''}
      <button class="favorite-btn ${this.favorites.has(content.id) ? 'active' : ''}" 
              data-content-id="${content.id}">
        <i class="fas fa-heart"></i>
      </button>
      ${epgLineSection}
    `;

    requestAnimationFrame(() => {
      const nameEl = item.querySelector('.content-name');
      const wrapperEl = item.querySelector('.content-name-wrapper');
      if (nameEl && wrapperEl && nameEl.scrollWidth > wrapperEl.clientWidth) {
        nameEl.classList.add('scrolling');
      }
    });

    if (type === 'channel' && isPlaying && content.id) {
      this.loadEPGLine(item, content.id, content.name);
    }

    item.addEventListener('click', (e) => {
      if (!e.target.classList.contains('favorite-btn') && !e.target.closest('.favorite-btn')) {
        if (type === 'channel') {
          this.playChannel(content);
        } else if (type === 'movie') {
          this.playMovie(content);
        } else if (type === 'series') {
          this.showSeriesEpisodes(content);
        } else if (type === 'radio') {
          this.playRadio(content);
        }
      }
    });

    const favoriteBtn = item.querySelector('.favorite-btn');
    favoriteBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      this.toggleFavorite(content.id);
    });

    return item;
  }

  // === EPG FUNCTIONS ===
  
  async loadEPGLine(itemElement, streamId, channelName) {
    const epgLine = itemElement.querySelector('.epg-line');
    if (!epgLine) return;
    
    const epgData = await this.fetchChannelEPG(streamId);
    
    if (epgData && epgData.current) {
      const startTime = this.formatEPGTime(epgData.current.start);
      const endTime = this.formatEPGTime(epgData.current.end);
      
      let epgHTML = `
        <div class="epg-line-current">
          <i class="fas fa-play-circle epg-line-icon"></i>
          <div class="epg-title-wrapper">
            <span class="epg-line-program" data-title="${this.escapeHtml(epgData.current.title)}">${epgData.current.title}</span>
          </div>
          <span class="epg-line-time">${startTime} - ${endTime}</span>
        </div>
      `;
      
      if (epgData.next) {
        const nextStart = this.formatEPGTime(epgData.next.start);
        epgHTML += `
          <div class="epg-line-next">
            <i class="fas fa-clock epg-line-next-icon"></i>
            <span class="epg-line-next-label">A seguir:</span>
            <div class="epg-next-title-wrapper">
              <span class="epg-line-next-title" data-title="${this.escapeHtml(epgData.next.title)}">${epgData.next.title}</span>
            </div>
            <span class="epg-line-next-time">${nextStart}</span>
          </div>
        `;
      }
      
      epgLine.innerHTML = epgHTML;
      
      requestAnimationFrame(() => {
        const currentWrapper = epgLine.querySelector('.epg-title-wrapper');
        const currentProgram = epgLine.querySelector('.epg-line-program');
        if (currentWrapper && currentProgram && currentProgram.scrollWidth > currentWrapper.clientWidth) {
          currentWrapper.classList.add('overflow');
        }
        
        const nextWrapper = epgLine.querySelector('.epg-next-title-wrapper');
        const nextTitle = epgLine.querySelector('.epg-line-next-title');
        if (nextWrapper && nextTitle && nextTitle.scrollWidth > nextWrapper.clientWidth) {
          nextWrapper.classList.add('overflow');
        }
      });
    } else {
      epgLine.innerHTML = `
        <div class="epg-line-current">
          <i class="fas fa-play-circle epg-line-icon"></i>
          <span class="epg-line-loading">Sem programação disponível</span>
        </div>
      `;
    }
  }
  
  decodeBase64(str) {
    try {
      if (!str) return str;
      if (/^[A-Za-z0-9+/=]+$/.test(str) && str.length > 3) {
        const decoded = atob(str);
        return decodeURIComponent(escape(decoded));
      }
      return str;
    } catch (e) {
      return str;
    }
  }
  
  async fetchChannelEPG(streamId) {
    const cacheKey = `epg_${streamId}`;
    const cached = this.epgCache.get(cacheKey);
    
    if (cached && Date.now() - cached.timestamp < this.epgCacheExpiration) {
      return cached.data;
    }
    
    try {
      const url = `${this.config.server}/player_api.php?username=${this.config.username}&password=${this.config.password}&action=get_simple_data_table&stream_id=${streamId}`;
      
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Erro ao buscar EPG');
      }
      
      const data = await response.json();
      
      if (!data || !data.epg_listings || data.epg_listings.length === 0) {
        return null;
      }
      
      const now = Math.floor(Date.now() / 1000);
      const epgList = data.epg_listings;
      
      let currentProgram = null;
      let nextProgram = null;
      
      for (let i = 0; i < epgList.length; i++) {
        const program = epgList[i];
        const start = parseInt(program.start_timestamp);
        const end = parseInt(program.stop_timestamp);
        
        if (now >= start && now < end) {
          currentProgram = {
            title: this.decodeBase64(program.title),
            start: program.start,
            end: program.end,
            description: this.decodeBase64(program.description || '')
          };
          
          if (i + 1 < epgList.length) {
            const next = epgList[i + 1];
            nextProgram = {
              title: this.decodeBase64(next.title),
              start: next.start,
              end: next.end
            };
          }
          break;
        }
      }
      
      const epgData = { current: currentProgram, next: nextProgram };
      
      this.epgCache.set(cacheKey, {
        data: epgData,
        timestamp: Date.now()
      });
      
      return epgData;
      
    } catch (error) {
      console.error('Erro ao buscar EPG para stream', streamId, error);
      return null;
    }
  }
  
  formatEPGTime(timeStr) {
    if (!timeStr) return '';
    try {
      const parts = timeStr.split(' ');
      if (parts.length >= 2) {
        const timeParts = parts[1].split(':');
        return `${timeParts[0]}:${timeParts[1]}`;
      }
      return timeStr;
    } catch (e) {
      return timeStr;
    }
  }
  
  async updateChannelEPG(itemElement, streamId) {
    const epgContainer = itemElement.querySelector('.epg-info');
    if (!epgContainer) return;
    
    const epgData = await this.fetchChannelEPG(streamId);
    
    if (epgData && epgData.current) {
      const startTime = this.formatEPGTime(epgData.current.start);
      const endTime = this.formatEPGTime(epgData.current.end);
      
      let epgHTML = `
        <div class="epg-current">
          <i class="fas fa-tv epg-current-icon"></i>
          <span class="epg-current-title">${epgData.current.title}</span>
          <span class="epg-current-time">${startTime} - ${endTime}</span>
        </div>
      `;
      
      if (epgData.next) {
        const nextStart = this.formatEPGTime(epgData.next.start);
        epgHTML += `
          <div class="epg-next">
            <span class="epg-next-label">Depois:</span>
            <span class="epg-next-title">${epgData.next.title}</span>
            <span class="epg-current-time">${nextStart}</span>
          </div>
        `;
      }
      
      epgContainer.innerHTML = epgHTML;
    } else {
      epgContainer.innerHTML = '<span class="epg-no-data">Sem programação disponível</span>';
    }
  }

  // === PLAYBACK FUNCTIONS ===

  playChannel(channel) {
    try {
      const streamUrl = `${this.config.server}/live/${this.config.username}/${this.config.password}/${channel.id}.m3u8`;
      
      this.currentChannel = channel.id;
      this.currentMovie = null;
      this.currentSeries = null;
      this.currentEpisode = null;
      this.currentRadio = null;
      this.radioVideoMode = false;

      this.setupAdvancedPlayer(streamUrl, 'channel');

      // Usa MediaCompat se disponível
      if (typeof MediaCompat !== 'undefined') {
        this.player.ready(() => {
          MediaCompat.playMedia(this.player.el().querySelector('video'));
        });
      } else {
        this.player.ready(() => {
          this.player.play();
        });
      }

      document.getElementById('videoPlaceholder').style.display = 'none';
      this.renderChannels();
      this.hideCustomControls();
      this.hideRadioInfo();
      this.hideRadioVisualDisplay();
      
      // Inicia foreground service se disponível
      if (typeof ForegroundService !== 'undefined') {
        ForegroundService.start(channel.name, 'Canal ao vivo', channel.icon);
      }
    } catch (error) {
      console.error('Erro ao reproduzir canal:', error);
      this.showErrorOverlay('Erro ao reproduzir canal', () => this.playChannel(channel));
    }
  }

  playMovie(movie) {
    const progress = this.checkContinueWatching(movie, 'movie');
    
    const doPlay = (startTime = 0) => {
      try {
        const extension = movie.container_extension || 'mp4';
        const streamUrl = `${this.config.server}/movie/${this.config.username}/${this.config.password}/${movie.id}.${extension}`;
        
        this.currentMovie = movie;
        this.currentChannel = null;
        this.currentSeries = null;
        this.currentEpisode = null;
        this.currentRadio = null;
        this.radioVideoMode = false;

        this.setupAdvancedPlayer(streamUrl, 'movie');

        this.player.ready(() => {
          if (startTime > 0) {
            this.player.currentTime(startTime);
          }
          this.player.play();
        });

        document.getElementById('videoPlaceholder').style.display = 'none';
        this.renderMovies();
        this.hideCustomControls();
        this.hideRadioInfo();
        this.hideRadioVisualDisplay();
      } catch (error) {
        console.error('Erro ao reproduzir filme:', error);
        this.showErrorOverlay('Erro ao reproduzir filme', () => this.playMovie(movie));
      }
    };

    if (progress) {
      this.showContinueModal(progress, doPlay, () => doPlay(0));
    } else {
      doPlay();
    }
  }

  playRadio(radio) {
    try {
      const hasVideo = radio.video && radio.video.trim() !== '' && radio.video !== 'url_vídeo';
      const streamUrl = hasVideo ? radio.video : radio.url;
      const type = hasVideo ? 'radio-video' : 'radio';
      
      this.currentRadio = radio;
      this.currentChannel = null;
      this.currentMovie = null;
      this.currentSeries = null;
      this.currentEpisode = null;
      this.radioVideoMode = hasVideo;

      this.setupAdvancedPlayer(streamUrl, type);

      this.player.ready(() => {
        this.player.play();
      });

      document.getElementById('videoPlaceholder').style.display = 'none';
      
      if (hasVideo) {
        this.hideRadioInfo();
        this.hideRadioVisualDisplay();
      } else {
        this.showRadioInfo(radio);
        this.showRadioVisualDisplay(radio);
      }
      
      this.renderRadios();
      this.hideCustomControls();
      
      // Inicia foreground service
      if (typeof ForegroundService !== 'undefined') {
        ForegroundService.start(radio.name, radio.frequency || 'Rádio', radio.icon);
      }
    } catch (error) {
      console.error('Erro ao reproduzir rádio:', error);
      this.showErrorOverlay('Erro ao reproduzir rádio', () => this.playRadio(radio));
    }
  }

  showRadioInfo(radio) {
    const overlay = document.getElementById('radioInfoOverlay');
    const logo = document.getElementById('radioLogoSmall');
    const name = document.getElementById('radioNameSmall');
    const freq = document.getElementById('radioFrequencySmall');
    
    if (radio.icon) {
      logo.src = radio.icon;
      logo.style.display = 'block';
    } else {
      logo.style.display = 'none';
    }
    
    name.textContent = radio.name;
    freq.textContent = radio.frequency || '';
    
    overlay.classList.add('visible');
  }

  hideRadioInfo() {
    document.getElementById('radioInfoOverlay').classList.remove('visible');
  }

  showRadioVisualDisplay(radio) {
    const display = document.getElementById('radioVisualDisplay');
    const background = display.querySelector('.radio-background');
    const mainImage = display.querySelector('.radio-main-image');
    const mainName = display.querySelector('.radio-main-info h3');
    const mainFreq = display.querySelector('.radio-main-info p');
    
    if (radio.icon) {
      background.style.backgroundImage = `url('${radio.icon}')`;
      mainImage.src = radio.icon;
      mainImage.style.display = 'block';
    } else {
      background.style.backgroundImage = 'none';
      mainImage.style.display = 'none';
    }
    
    mainName.textContent = radio.name;
    mainFreq.textContent = radio.frequency || radio.city || '';
    
    display.classList.add('active');
  }

  hideRadioVisualDisplay() {
    document.getElementById('radioVisualDisplay').classList.remove('active');
  }

  async showSeriesEpisodes(series) {
    this.currentSeries = series;
    
    try {
      const response = await fetch(`${this.config.server}/player_api.php?username=${this.config.username}&password=${this.config.password}&action=get_series_info&series_id=${series.id}`);
      const data = await response.json();
      
      this.episodes = [];
      
      if (data.episodes) {
        Object.keys(data.episodes).forEach(season => {
          data.episodes[season].forEach(ep => {
            this.episodes.push({
              id: ep.id,
              title: ep.title || `Episódio ${ep.episode_num}`,
              season: season,
              episode_num: ep.episode_num,
              container_extension: ep.container_extension,
              url: `${this.config.server}/series/${this.config.username}/${this.config.password}/${ep.id}.${ep.container_extension}`
            });
          });
        });
      }
      
      const seriesList = document.getElementById('seriesList');
      const episodeList = document.getElementById('episodeList');
      
      seriesList.style.display = 'none';
      episodeList.style.display = 'grid';
      
      this.renderEpisodes();
    } catch (error) {
      console.error('Erro ao carregar episódios:', error);
      this.showErrorOverlay('Erro ao carregar episódios', () => this.showSeriesEpisodes(series));
    }
  }

  renderEpisodes() {
    const episodeList = document.getElementById('episodeList');
    
    episodeList.innerHTML = `
      <button class="episode-back-button" onclick="iptvApp.backToSeries()">
        <i class="fas fa-arrow-left"></i>
        Voltar para Séries
      </button>
    `;
    
    this.episodes.forEach((episode, index) => {
      const card = document.createElement('div');
      card.className = 'episode-card';
      
      if (this.currentEpisode && this.currentEpisode.id === episode.id) {
        card.classList.add('playing');
      }
      
      card.innerHTML = `
        <div class="episode-title">T${episode.season}E${episode.episode_num}</div>
        <div class="episode-info">${episode.title}</div>
      `;
      
      card.addEventListener('click', () => this.playEpisode(episode, index));
      episodeList.appendChild(card);
    });
  }

  playEpisode(episode, index) {
    const progress = this.checkContinueWatching(episode, 'episode');
    
    const doPlay = (startTime = 0) => {
      try {
        this.currentEpisode = episode;
        this.currentEpisodeIndex = index;
        this.currentChannel = null;
        this.currentMovie = null;
        this.currentRadio = null;

        this.setupAdvancedPlayer(episode.url, 'episode');

        this.player.ready(() => {
          if (startTime > 0) {
            this.player.currentTime(startTime);
          }
          this.player.play();
        });

        document.getElementById('videoPlaceholder').style.display = 'none';
        this.renderEpisodes();
        this.showCustomControls();
        this.updateEpisodeNavigation();
        this.hideRadioInfo();
        this.hideRadioVisualDisplay();
      } catch (error) {
        console.error('Erro ao reproduzir episódio:', error);
        this.showErrorOverlay('Erro ao reproduzir episódio', () => this.playEpisode(episode, index));
      }
    };

    if (progress) {
      this.showContinueModal(progress, doPlay, () => doPlay(0));
    } else {
      doPlay();
    }
  }

  backToSeries() {
    const episodeList = document.getElementById('episodeList');
    const seriesList = document.getElementById('seriesList');
    
    episodeList.style.display = 'none';
    seriesList.style.display = 'block';
    
    this.hideCustomControls();
    this.currentSeries = null;
    this.currentEpisode = null;
    this.episodes = [];
    
    this.renderSeries();
    
    console.log('Voltou para lista de séries');
  }

  showCustomControls() {
    document.getElementById('customControls').style.display = 'flex';
    this.updateNavigationButtons();
  }

  hideCustomControls() {
    document.getElementById('customControls').style.display = 'none';
    this.hideEpisodeNavigation();
  }

  updateNavigationButtons() {
    const prevBtn = document.getElementById('prevEpisodeBtn');
    const nextBtn = document.getElementById('nextEpisodeBtn');
    
    prevBtn.disabled = this.currentEpisodeIndex <= 0;
    nextBtn.disabled = this.currentEpisodeIndex >= this.episodes.length - 1;
  }

  playPreviousEpisode() {
    if (this.currentEpisodeIndex > 0) {
      const prevIndex = this.currentEpisodeIndex - 1;
      this.playEpisode(this.episodes[prevIndex], prevIndex);
    }
  }

  playNextEpisode() {
    if (this.currentEpisodeIndex < this.episodes.length - 1) {
      const nextIndex = this.currentEpisodeIndex + 1;
      this.playEpisode(this.episodes[nextIndex], nextIndex);
    }
  }

  toggleEpisodeNavigation() {
    const overlay = document.getElementById('episodeNavOverlay');
    if (overlay.classList.contains('visible')) {
      this.hideEpisodeNavigation();
    } else {
      this.showEpisodeNavigation();
    }
  }

  showEpisodeNavigation() {
    if (!this.currentSeries || this.episodes.length === 0) return;

    const overlay = document.getElementById('episodeNavOverlay');
    const title = document.getElementById('episodeNavTitle');
    const list = document.getElementById('episodeNavList');

    title.textContent = this.currentSeries.name;
    list.innerHTML = '';

    this.episodes.forEach((episode, index) => {
      const item = document.createElement('button');
      item.className = 'episode-nav-item';
      
      if (this.currentEpisode && this.currentEpisode.id === episode.id) {
        item.classList.add('current');
      }

      item.textContent = `T${episode.season}E${episode.episode_num} - ${episode.title}`;
      item.addEventListener('click', () => {
        this.playEpisode(episode, index);
        this.hideEpisodeNavigation();
      });

      list.appendChild(item);
    });

    overlay.classList.add('visible');
  }

  hideEpisodeNavigation() {
    document.getElementById('episodeNavOverlay').classList.remove('visible');
  }

  updateEpisodeNavigation() {
    if (document.getElementById('episodeNavOverlay').classList.contains('visible')) {
      this.showEpisodeNavigation();
    }
  }

  // === WATCH PROGRESS ===

  checkContinueWatching(content, type) {
    const progressKey = type === 'channel' ? `channel_${content.id || content}` : 
                       type === 'movie' ? `movie_${content.id}` : 
                       type === 'series' ? `series_${content.id}` :
                       type === 'episode' ? `episode_${content.id}` :
                       `radio_${content.id}`;
                       
    const progress = this.watchProgress.get(progressKey);
    
    if (progress && progress.percentage > 5 && progress.percentage < 90) {
      return {
        time: progress.currentTime,
        percentage: progress.percentage,
        duration: progress.duration
      };
    }
    
    return null;
  }

  showContinueModal(progress, continueCallback, restartCallback) {
    const modal = document.getElementById('continueModal');
    const message = document.getElementById('continueMessage');
    
    message.textContent = `Você parou em ${Math.round(progress.percentage)}% do conteúdo`;
    
    this.pendingContinueAction = {
      continue: () => continueCallback(progress.time),
      restart: () => restartCallback()
    };
    
    modal.style.display = 'flex';
  }

  saveWatchProgress() {
    if (!this.player || this.player.paused()) return;
    
    const currentTime = this.player.currentTime();
    const duration = this.player.duration();
    
    if (!currentTime || !duration || currentTime < 30) return;
    
    const percentage = (currentTime / duration) * 100;
    
    let progressKey = '';
    if (this.currentChannel) {
      progressKey = `channel_${this.currentChannel}`;
    } else if (this.currentMovie) {
      progressKey = `movie_${this.currentMovie.id}`;
    } else if (this.currentEpisode) {
      progressKey = `episode_${this.currentEpisode.id}`;
    } else if (this.currentRadio) {
      progressKey = `radio_${this.currentRadio.id}`;
    }
    
    if (progressKey) {
      this.watchProgress.set(progressKey, {
        currentTime,
        duration,
        percentage,
        timestamp: Date.now()
      });
      
      this.saveWatchProgressToStorage();
    }
  }

  loadWatchProgress() {
    try {
      let saved;
      if (typeof StorageCompat !== 'undefined') {
        saved = StorageCompat.getItem('iptv-watch-progress');
      } else {
        saved = localStorage.getItem('iptv-watch-progress');
      }
      
      if (saved) {
        const data = JSON.parse(saved);
        this.watchProgress = new Map(data);
      }
    } catch (error) {
      console.error('Erro ao carregar progresso:', error);
    }
  }

  saveWatchProgressToStorage() {
    try {
      const data = Array.from(this.watchProgress.entries());
      
      if (typeof StorageCompat !== 'undefined') {
        StorageCompat.setItem('iptv-watch-progress', JSON.stringify(data));
      } else {
        localStorage.setItem('iptv-watch-progress', JSON.stringify(data));
      }
    } catch (error) {
      console.error('Erro ao salvar progresso:', error);
    }
  }

  // === FAVORITES ===

  toggleFavorite(itemId) {
    let item = null;
    let itemType = null;
    
    item = this.channels.find(c => c.id === itemId);
    if (item) itemType = 'channel';
    
    if (!item) {
      item = this.movies.find(m => m.id === itemId);
      if (item) itemType = 'movie';
    }
    
    if (!item) {
      item = this.series.find(s => s.id === itemId);
      if (item) itemType = 'series';
    }
    
    if (!item) {
      item = this.radios.find(r => r.id === itemId);
      if (item) itemType = 'radio';
    }
    
    if (!item) {
      const favoriteItem = this.favoritesBackend.getFavorites().find(f => f.id === itemId);
      if (favoriteItem) {
        item = favoriteItem;
        itemType = favoriteItem.type;
      }
    }
    
    if (!item) {
      console.warn('Item não encontrado para toggle favorite:', itemId);
      return;
    }
    
    const wasFavorite = this.favoritesBackend.isFavorite(itemId);
    
    if (wasFavorite) {
      console.log('Removendo favorito:', itemId);
      this.favoritesBackend.removeFavorite(itemId);
      this.favorites.delete(itemId);
      this.showToast(`Removido dos favoritos: ${item.name}`, 'success');
    } else {
      console.log('Adicionando favorito:', itemId);
      this.favoritesBackend.addFavorite(itemId, { ...item, type: itemType });
      this.favorites.add(itemId);
      this.showToast(`Adicionado aos favoritos: ${item.name}`, 'success');
    }
    
    this.updateAllFavoriteButtons();
    
    if (this.activeContent === 'channels') {
      this.renderChannels();
    } else if (this.activeContent === 'movies') {
      this.renderMovies();
    } else if (this.activeContent === 'series') {
      this.renderSeries();
    } else if (this.activeContent === 'radios') {
      this.renderRadios();
    } else if (this.activeContent === 'favorites') {
      this.renderFavorites();
    }
  }

  loadFavorites() {
    try {
      const backendFavorites = this.favoritesBackend.getFavorites();
      this.favorites = new Set(backendFavorites.map(item => item.id));
      
      let saved;
      if (typeof StorageCompat !== 'undefined') {
        saved = StorageCompat.getItem('iptv-favorites');
      } else {
        saved = localStorage.getItem('iptv-favorites');
      }
      
      if (saved) {
        const oldFavorites = JSON.parse(saved);
        oldFavorites.forEach(id => {
          if (!this.favorites.has(id)) {
            this.favorites.add(id);
          }
        });
      }
    } catch (error) {
      console.error('Erro ao carregar favoritos:', error);
    }
  }

  saveFavorites() {
    try {
      if (typeof StorageCompat !== 'undefined') {
        StorageCompat.setItem('iptv-favorites', JSON.stringify([...this.favorites]));
      } else {
        localStorage.setItem('iptv-favorites', JSON.stringify([...this.favorites]));
      }
    } catch (error) {
      console.error('Erro ao salvar favoritos:', error);
    }
  }

  renderFavorites() {
    const favoritesList = document.getElementById('favoritesList');
    const favorites = this.favoritesBackend.getFavorites();
    
    console.log('Renderizando favoritos:', favorites.length);
    
    if (favorites.length === 0) {
      favoritesList.innerHTML = `
        <div class="favorites-empty">
          <i class="fas fa-heart"></i>
          <h5>Nenhum favorito ainda</h5>
          <p>Toque no ❤️ nos seus conteúdos preferidos para vê-los aqui!</p>
        </div>
      `;
      return;
    }
    
    favoritesList.innerHTML = '';
    
    favorites.forEach(favorite => {
      const card = document.createElement('div');
      card.className = 'favorite-card';
      
      const avatarStyle = favorite.icon ? 
        `background-image: url('${favorite.icon}'); background-size: cover; background-position: center;` : 
        '';
      
      const typeLabels = {
        'channel': '📺 Canal',
        'movie': '🎬 Filme', 
        'series': '📺 Série',
        'radio': '📻 Rádio'
      };
      
      const favoriteDate = new Date(favorite.favoriteDate).toLocaleDateString('pt-BR');
      
      card.innerHTML = `
        <div class="favorite-header">
          <div class="favorite-avatar" style="${avatarStyle}">
            ${!favorite.icon ? favorite.letter || favorite.name.charAt(0).toUpperCase() : ''}
          </div>
          <div class="favorite-info">
            <h6>${favorite.name}</h6>
            <small>
              ${typeLabels[favorite.type] || favorite.type}
              ${favorite.year ? ` • ${favorite.year}` : ''}
              ${favorite.rating ? ` • ⭐ ${favorite.rating}` : ''}
            </small>
          </div>
        </div>
        
        <div class="favorite-actions">
          <button class="play-btn" data-favorite-id="${favorite.id}" data-favorite-type="${favorite.type}">
            <i class="fas fa-play"></i>
            Reproduzir
          </button>
          <button class="remove-favorite" data-favorite-id="${favorite.id}" title="Remover dos favoritos">
            <i class="fas fa-trash"></i>
          </button>
        </div>
        
        <div class="favorite-meta">
          Favoritado em ${favoriteDate}
        </div>
      `;
      
      const playBtn = card.querySelector('.play-btn');
      playBtn.addEventListener('click', () => {
        this.favoritesBackend.updateLastAccessed(favorite.id);
        this.playFavoriteItem(favorite);
      });
      
      const removeBtn = card.querySelector('.remove-favorite');
      removeBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        if (confirm(`Tem certeza que deseja remover "${favorite.name}" dos favoritos?`)) {
          console.log('Removendo favorito via botão remove:', favorite.id);
          this.toggleFavorite(favorite.id);
        }
      });
      
      favoritesList.appendChild(card);
    });
  }

  updateAllFavoriteButtons() {
    document.querySelectorAll('.favorite-btn').forEach(btn => {
      const itemId = btn.dataset.id || btn.closest('.content-item').dataset.id;
      if (itemId) {
        const isFav = this.favoritesBackend.isFavorite(itemId);
        btn.innerHTML = isFav ? '<i class="fas fa-heart"></i>' : '<i class="far fa-heart"></i>';
        btn.classList.toggle('favorited', isFav);
      }
    });
  }

  showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: ${type === 'success' ? '#28a745' : '#007bff'};
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      z-index: 10000;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      transform: translateX(100%);
      transition: transform 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.style.transform = 'translateX(0)';
    }, 100);
    
    setTimeout(() => {
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => {
        if (toast.parentNode) {
          toast.parentNode.removeChild(toast);
        }
      }, 300);
    }, 3000);
  }
  
  playFavoriteItem(favorite) {
    if (favorite.type === 'channel') {
      this.showContentSection('channels');
      this.playChannel(favorite);
      document.querySelector('[data-content="channels"]').classList.add('active');
      document.querySelectorAll('.main-nav .nav-link:not([data-content="channels"])').forEach(l => l.classList.remove('active'));
    } else if (favorite.type === 'movie') {
      this.showContentSection('movies');
      this.playMovie(favorite);
      document.querySelector('[data-content="movies"]').classList.add('active');
      document.querySelectorAll('.main-nav .nav-link:not([data-content="movies"])').forEach(l => l.classList.remove('active'));
    } else if (favorite.type === 'series') {
      this.showContentSection('series');
      this.showSeriesEpisodes(favorite);
      document.querySelector('[data-content="series"]').classList.add('active');
      document.querySelectorAll('.main-nav .nav-link:not([data-content="series"])').forEach(l => l.classList.remove('active'));
    } else if (favorite.type === 'radio') {
      this.showContentSection('radios');
      this.playRadio(favorite);
      document.querySelector('[data-content="radios"]').classList.add('active');
      document.querySelectorAll('.main-nav .nav-link:not([data-content="radios"])').forEach(l => l.classList.remove('active'));
    }
  }

  // === SEARCH ===

  performSearch(query) {
    const resultsContainer = document.getElementById('searchResults');
    
    if (!query || query.length < 2) {
      resultsContainer.innerHTML = `
        <div class="text-center">
          <i class="fas fa-search fa-2x mb-2" style="color: #666;"></i>
          <p>Digite pelo menos 2 caracteres para buscar</p>
        </div>
      `;
      return;
    }

    const searchChannels = document.getElementById('searchChannels').checked;
    const searchMovies = document.getElementById('searchMovies').checked;
    const searchSeries = document.getElementById('searchSeries').checked;
    const searchRadios = document.getElementById('searchRadios').checked;

    let results = [];
    
    if (searchChannels) {
      results.push(...this.channels.filter(item => 
        item.name.toLowerCase().includes(query.toLowerCase())
      ));
    }
    
    if (searchMovies) {
      results.push(...this.movies.filter(item => 
        item.name.toLowerCase().includes(query.toLowerCase())
      ));
    }
    
    if (searchSeries) {
      results.push(...this.series.filter(item => 
        item.name.toLowerCase().includes(query.toLowerCase())
      ));
    }
    
    if (searchRadios) {
      results.push(...this.radios.filter(item => 
        item.name.toLowerCase().includes(query.toLowerCase())
      ));
    }

    if (results.length === 0) {
      resultsContainer.innerHTML = `
        <div class="text-center p-4">
          <i class="fas fa-search fa-2x mb-2" style="color: #666;"></i>
          <p>Nenhum resultado encontrado para "${query}"</p>
        </div>
      `;
      return;
    }

    resultsContainer.innerHTML = '';
    results.slice(0, 50).forEach(item => {
      const searchItem = document.createElement('div');
      searchItem.className = 'search-item';
      
      const iconStyle = item.icon ? `background-image: url('${item.icon}'); background-size: cover; background-position: center;` : '';
      
      searchItem.innerHTML = `
        <div class="item-icon" style="${iconStyle}">
          ${!item.icon ? item.letter : ''}
        </div>
        <div class="item-info">
          <div class="item-name">${item.name}</div>
          <div class="item-type">${this.getTypeLabel(item.type)}</div>
        </div>
      `;

      searchItem.addEventListener('click', () => {
        const modal = bootstrap.Modal.getInstance(document.getElementById('searchModal'));
        modal.hide();
        
        if (item.type === 'channel') {
          this.showContentSection('channels');
          this.playChannel(item);
        } else if (item.type === 'movie') {
          this.showContentSection('movies');
          this.playMovie(item);
        } else if (item.type === 'series') {
          this.showContentSection('series');
          this.showSeriesEpisodes(item);
        } else if (item.type === 'radio') {
          this.showContentSection('radios');
          this.playRadio(item);
        }
        
        document.querySelectorAll('.main-nav .nav-link').forEach(l => l.classList.remove('active'));
        const targetContent = item.type === 'channel' ? 'channels' : 
                             item.type === 'movie' ? 'movies' : 
                             item.type === 'series' ? 'series' : 'radios';
        document.querySelector(`[data-content="${targetContent}"]`).classList.add('active');
      });

      resultsContainer.appendChild(searchItem);
    });
  }

  getTypeLabel(type) {
    const labels = {
      'channel': 'Canal',
      'movie': 'Filme',
      'series': 'Série',
      'radio': 'Rádio'
    };
    return labels[type] || type;
  }

  // === PLAYLIST ===

  async savePlaylist() {
    try {
      const url = document.getElementById('playlistUrl').value.trim();
      if (!url) {
        this.showError('Por favor, insira uma URL válida');
        return;
      }

      const newConfig = this.extractPlaylistInfo(url);
      this.config = newConfig;
      this.saveConfig();

      const modal = bootstrap.Modal.getInstance(document.getElementById('playlistModal'));
      modal.hide();
      document.getElementById('playlistForm').reset();

      this.cache.clear();

      await Promise.all([
        this.loadCategories(),
        this.loadMovieCategories(),
        this.loadSeriesCategories()
      ]);

      this.showSuccess('Playlist adicionada com sucesso!');
    } catch (error) {
      console.error('Erro ao salvar playlist:', error);
      this.showError(error.message);
    }
  }

  extractPlaylistInfo(url) {
    try {
      const urlObj = new URL(url);
      const server = `${urlObj.protocol}//${urlObj.host}`;
      const username = urlObj.searchParams.get('username');
      const password = urlObj.searchParams.get('password');

      if (!username || !password) {
        throw new Error('Username ou password não encontrado na URL');
      }

      return { server, username, password };
    } catch (error) {
      throw new Error('URL inválida. Verifique se contém username e password.');
    }
  }

  // === SHARE ===

  shareApp() {
    const shareUrl = window.location.href;
    
    if (navigator.share) {
      navigator.share({
        title: 'IPTV Player 3 - Canais, Filmes e Séries',
        text: 'Assista canais brasileiros, filmes e séries online',
        url: shareUrl
      }).catch(console.error);
    } else {
      navigator.clipboard.writeText(shareUrl).then(() => {
        this.showSuccess('Link copiado para a área de transferência!');
      }).catch(() => {
        this.showError('Não foi possível copiar o link');
      });
    }
  }

  // === ERROR HANDLING ===

  showErrorOverlay(message, retryCallback) {
    const overlay = document.getElementById('errorOverlay');
    const messageEl = document.getElementById('errorMessage');
    
    messageEl.textContent = message;
    this.pendingRetryAction = retryCallback;
    overlay.style.display = 'flex';
  }

  showError(message) {
    this.showAlert('Erro', message, 'error');
  }

  showSuccess(message) {
    this.showAlert('Sucesso', message, 'success');
  }

  showAlert(title, message, type = 'info') {
    document.querySelectorAll('.custom-alert, .alert-backdrop').forEach(el => el.remove());

    const backdrop = document.createElement('div');
    backdrop.className = 'alert-backdrop';
    backdrop.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0,0,0,0.8);
      z-index: 9998;
      display: flex;
      align-items: center;
      justify-content: center;
    `;

    const alert = document.createElement('div');
    alert.className = 'custom-alert';
    alert.style.cssText = `
      background: var(--bg-tertiary);
      color: white;
      padding: 2rem;
      border-radius: 1rem;
      text-align: center;
      max-width: 90%;
      width: 400px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    `;

    const iconColor = type === 'error' ? '#EF4444' : type === 'success' ? '#10B981' : '#6B7280';
    const iconName = type === 'error' ? 'exclamation-triangle' : type === 'success' ? 'check-circle' : 'info-circle';

    alert.innerHTML = `
      <i class="fas fa-${iconName} fa-3x mb-3" style="color: ${iconColor}"></i>
      <h5 class="mb-3">${title}</h5>
      <p class="mb-4">${message}</p>
      <button class="btn btn-${type === 'error' ? 'danger' : 'success'}" onclick="this.closest('.alert-backdrop').remove()">
        OK
      </button>
    `;

    backdrop.appendChild(alert);
    document.body.appendChild(backdrop);

    if (type === 'success') {
      setTimeout(() => {
        if (backdrop.parentNode) {
          backdrop.remove();
        }
      }, 5000);
    }
  }

  async loadGames() {
    try {
      const games = [];
      
      const gamesScroll = document.getElementById('gamesScroll');
      gamesScroll.textContent = games.join(' • ');
    } catch (error) {
      console.error('Erro ao carregar jogos:', error);
    }
  }
}

/* ========================================
   INITIALIZATION
   ======================================== */

let iptvApp;

document.addEventListener('DOMContentLoaded', () => {
  // Proteção contra cópia
  document.addEventListener('contextmenu', function(e) {
    e.preventDefault();
    return false;
  });
  
  document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && (e.keyCode === 67 || e.keyCode === 65 || e.keyCode === 83 || e.keyCode === 85)) {
      e.preventDefault();
      return false;
    }
    if (e.keyCode === 123) {
      e.preventDefault();
      return false;
    }
  });
  
  document.addEventListener('selectstart', function(e) {
    e.preventDefault();
    return false;
  });
  
  document.addEventListener('dragstart', function(e) {
    e.preventDefault();
    return false;
  });
  
  loadTheme();
  loadPageBackground();
  iptvApp = new IPTVApp();
});
