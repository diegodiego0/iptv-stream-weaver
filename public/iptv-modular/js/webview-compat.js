/**
 * =============================================
 * CAMADA DE COMPATIBILIDADE ANDROID WEBVIEW
 * =============================================
 * Este arquivo adiciona suporte para:
 * - Fullscreen com fallback para WebView
 * - Persistência de localStorage
 * - Eventos de clique otimizados para touch
 * - Media playback sem interação do usuário
 * - Navegação de links internos/externos
 * - Comunicação com Android via JavaScriptInterface
 * 
 * Compatível com:
 * - Android WebView (API 21+)
 * - Sketchware padrão e modificado
 * - Navegadores desktop (Chrome, Firefox, Safari)
 * =============================================
 */

(function() {
  'use strict';

  // === DETECÇÃO DE AMBIENTE ===
  const WebViewCompat = {
    isAndroidWebView: function() {
      return typeof Android !== 'undefined' || 
             /Android/.test(navigator.userAgent) && /wv/.test(navigator.userAgent);
    },
    
    isSketchware: function() {
      return typeof Android !== 'undefined' && typeof Android.isSketchware === 'function';
    },
    
    isMobile: function() {
      return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    },
    
    supportsLocalStorage: function() {
      try {
        const test = '__storage_test__';
        localStorage.setItem(test, test);
        localStorage.removeItem(test);
        return true;
      } catch (e) {
        return false;
      }
    }
  };

  // === FULLSCREEN COMPATIBILITY ===
  const FullscreenCompat = {
    /**
     * Solicita fullscreen com fallbacks para diferentes navegadores e WebView
     */
    requestFullscreen: function(element) {
      element = element || document.documentElement;
      
      // Tenta comunicação com Android nativo primeiro
      if (typeof Android !== 'undefined' && typeof Android.requestFullscreen === 'function') {
        try {
          Android.requestFullscreen();
          return Promise.resolve();
        } catch (e) {
          console.log('Android fullscreen não disponível, usando fallback');
        }
      }
      
      // Fallbacks para diferentes navegadores
      const methods = [
        'requestFullscreen',
        'webkitRequestFullscreen',
        'webkitEnterFullscreen',
        'mozRequestFullScreen',
        'msRequestFullscreen'
      ];
      
      for (const method of methods) {
        if (typeof element[method] === 'function') {
          try {
            const result = element[method]();
            if (result instanceof Promise) {
              return result;
            }
            return Promise.resolve();
          } catch (e) {
            continue;
          }
        }
      }
      
      // Fallback para vídeo em WebView iOS
      if (element.tagName === 'VIDEO' && element.webkitEnterFullscreen) {
        element.webkitEnterFullscreen();
        return Promise.resolve();
      }
      
      // Último fallback: simula fullscreen com CSS
      this._simulateFullscreen(element);
      return Promise.resolve();
    },
    
    /**
     * Sai do fullscreen
     */
    exitFullscreen: function() {
      if (typeof Android !== 'undefined' && typeof Android.exitFullscreen === 'function') {
        try {
          Android.exitFullscreen();
          return Promise.resolve();
        } catch (e) {
          console.log('Android exitFullscreen não disponível');
        }
      }
      
      const methods = [
        'exitFullscreen',
        'webkitExitFullscreen',
        'mozCancelFullScreen',
        'msExitFullscreen'
      ];
      
      for (const method of methods) {
        if (typeof document[method] === 'function') {
          try {
            const result = document[method]();
            if (result instanceof Promise) {
              return result;
            }
            return Promise.resolve();
          } catch (e) {
            continue;
          }
        }
      }
      
      this._exitSimulatedFullscreen();
      return Promise.resolve();
    },
    
    /**
     * Verifica se está em fullscreen
     */
    isFullscreen: function() {
      return !!(
        document.fullscreenElement ||
        document.webkitFullscreenElement ||
        document.mozFullScreenElement ||
        document.msFullscreenElement ||
        document.body.classList.contains('simulated-fullscreen')
      );
    },
    
    /**
     * Toggle fullscreen
     */
    toggleFullscreen: function(element) {
      if (this.isFullscreen()) {
        return this.exitFullscreen();
      }
      return this.requestFullscreen(element);
    },
    
    /**
     * Simula fullscreen via CSS quando API não está disponível
     */
    _simulateFullscreen: function(element) {
      if (!document.getElementById('simulated-fullscreen-styles')) {
        const style = document.createElement('style');
        style.id = 'simulated-fullscreen-styles';
        style.textContent = `
          .simulated-fullscreen {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            z-index: 999999 !important;
            background: #000 !important;
          }
          body.simulated-fullscreen-active {
            overflow: hidden !important;
          }
        `;
        document.head.appendChild(style);
      }
      
      element.classList.add('simulated-fullscreen');
      document.body.classList.add('simulated-fullscreen-active');
      
      // Dispatch evento customizado
      element.dispatchEvent(new Event('fullscreenchange'));
    },
    
    _exitSimulatedFullscreen: function() {
      document.querySelectorAll('.simulated-fullscreen').forEach(el => {
        el.classList.remove('simulated-fullscreen');
      });
      document.body.classList.remove('simulated-fullscreen-active');
    }
  };

  // === STORAGE COMPATIBILITY ===
  const StorageCompat = {
    _memoryStorage: {},
    
    /**
     * Obtém item do storage com fallbacks
     */
    getItem: function(key) {
      // Tenta Android storage primeiro
      if (typeof Android !== 'undefined' && typeof Android.getStorage === 'function') {
        try {
          return Android.getStorage(key);
        } catch (e) {
          console.log('Android storage não disponível');
        }
      }
      
      // Tenta localStorage
      if (WebViewCompat.supportsLocalStorage()) {
        try {
          return localStorage.getItem(key);
        } catch (e) {
          console.log('localStorage não disponível');
        }
      }
      
      // Fallback para memória
      return this._memoryStorage[key] || null;
    },
    
    /**
     * Salva item no storage com fallbacks
     */
    setItem: function(key, value) {
      // Tenta Android storage primeiro
      if (typeof Android !== 'undefined' && typeof Android.setStorage === 'function') {
        try {
          Android.setStorage(key, value);
        } catch (e) {
          console.log('Android setStorage não disponível');
        }
      }
      
      // Tenta localStorage
      if (WebViewCompat.supportsLocalStorage()) {
        try {
          localStorage.setItem(key, value);
          return;
        } catch (e) {
          console.log('localStorage setItem falhou');
        }
      }
      
      // Fallback para memória
      this._memoryStorage[key] = value;
    },
    
    /**
     * Remove item do storage
     */
    removeItem: function(key) {
      if (typeof Android !== 'undefined' && typeof Android.removeStorage === 'function') {
        try {
          Android.removeStorage(key);
        } catch (e) {}
      }
      
      if (WebViewCompat.supportsLocalStorage()) {
        try {
          localStorage.removeItem(key);
        } catch (e) {}
      }
      
      delete this._memoryStorage[key];
    },
    
    /**
     * Limpa todo o storage
     */
    clear: function() {
      if (typeof Android !== 'undefined' && typeof Android.clearStorage === 'function') {
        try {
          Android.clearStorage();
        } catch (e) {}
      }
      
      if (WebViewCompat.supportsLocalStorage()) {
        try {
          localStorage.clear();
        } catch (e) {}
      }
      
      this._memoryStorage = {};
    }
  };

  // === TOUCH/CLICK COMPATIBILITY ===
  const TouchCompat = {
    /**
     * Adiciona eventos de clique otimizados para touch
     */
    addClickListener: function(element, callback, options) {
      options = options || {};
      
      if (!element) return;
      
      // Usa 'touchend' em mobile para resposta mais rápida
      if (WebViewCompat.isMobile()) {
        let touchStartX, touchStartY;
        
        element.addEventListener('touchstart', function(e) {
          touchStartX = e.touches[0].clientX;
          touchStartY = e.touches[0].clientY;
        }, { passive: true });
        
        element.addEventListener('touchend', function(e) {
          const touchEndX = e.changedTouches[0].clientX;
          const touchEndY = e.changedTouches[0].clientY;
          
          // Verifica se foi um tap (não scroll)
          const deltaX = Math.abs(touchEndX - touchStartX);
          const deltaY = Math.abs(touchEndY - touchStartY);
          
          if (deltaX < 10 && deltaY < 10) {
            if (!options.allowDefault) {
              e.preventDefault();
            }
            callback.call(element, e);
          }
        }, { passive: false });
      } else {
        element.addEventListener('click', callback);
      }
    },
    
    /**
     * Remove delay de 300ms em cliques mobile
     */
    fastClick: function() {
      if (!WebViewCompat.isMobile()) return;
      
      // Adiciona touch-action CSS para remover delay
      if (!document.getElementById('fastclick-styles')) {
        const style = document.createElement('style');
        style.id = 'fastclick-styles';
        style.textContent = `
          * {
            touch-action: manipulation;
          }
        `;
        document.head.appendChild(style);
      }
    }
  };

  // === MEDIA PLAYBACK COMPATIBILITY ===
  const MediaCompat = {
    /**
     * Tenta reproduzir mídia com handling de políticas de autoplay
     */
    playMedia: function(mediaElement) {
      if (!mediaElement) return Promise.reject('Elemento de mídia não encontrado');
      
      // Garante que está unmuted para autoplay funcionar
      const originalMuted = mediaElement.muted;
      
      const attemptPlay = function() {
        const playPromise = mediaElement.play();
        
        if (playPromise !== undefined) {
          return playPromise.catch(function(error) {
            if (error.name === 'NotAllowedError') {
              // Tenta com muted
              mediaElement.muted = true;
              return mediaElement.play().then(function() {
                // Se funcionou com muted, tenta unmute após um tempo
                setTimeout(function() {
                  mediaElement.muted = originalMuted;
                }, 1000);
              });
            }
            throw error;
          });
        }
        
        return Promise.resolve();
      };
      
      // Notifica Android se disponível
      if (typeof Android !== 'undefined' && typeof Android.onMediaPlay === 'function') {
        try {
          Android.onMediaPlay(mediaElement.src);
        } catch (e) {}
      }
      
      return attemptPlay();
    },
    
    /**
     * Pausa mídia e notifica Android
     */
    pauseMedia: function(mediaElement) {
      if (!mediaElement) return;
      
      mediaElement.pause();
      
      if (typeof Android !== 'undefined' && typeof Android.onMediaPause === 'function') {
        try {
          Android.onMediaPause();
        } catch (e) {}
      }
    },
    
    /**
     * Para mídia e notifica Android
     */
    stopMedia: function(mediaElement) {
      if (!mediaElement) return;
      
      mediaElement.pause();
      mediaElement.currentTime = 0;
      
      if (typeof Android !== 'undefined' && typeof Android.onMediaStop === 'function') {
        try {
          Android.onMediaStop();
        } catch (e) {}
      }
    }
  };

  // === NAVIGATION COMPATIBILITY ===
  const NavigationCompat = {
    /**
     * Abre link interno ou externo
     */
    openLink: function(url, target) {
      target = target || '_self';
      
      // Links externos no Android
      if (target === '_blank' || this.isExternalLink(url)) {
        if (typeof Android !== 'undefined' && typeof Android.openExternalLink === 'function') {
          try {
            Android.openExternalLink(url);
            return;
          } catch (e) {}
        }
        
        window.open(url, '_blank');
        return;
      }
      
      // Links internos
      if (url.startsWith('#')) {
        const element = document.querySelector(url);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth' });
        }
        return;
      }
      
      // Navegação normal
      window.location.href = url;
    },
    
    /**
     * Verifica se é link externo
     */
    isExternalLink: function(url) {
      if (!url) return false;
      
      // Links absolutos com protocolo diferente
      if (/^(http|https|ftp|mailto|tel):/.test(url)) {
        try {
          const linkHost = new URL(url).hostname;
          return linkHost !== window.location.hostname;
        } catch (e) {
          return true;
        }
      }
      
      return false;
    },
    
    /**
     * Volta na navegação
     */
    goBack: function() {
      if (typeof Android !== 'undefined' && typeof Android.goBack === 'function') {
        try {
          Android.goBack();
          return;
        } catch (e) {}
      }
      
      if (window.history.length > 1) {
        window.history.back();
      }
    }
  };

  // === FOREGROUND SERVICE (BACKGROUND PLAYBACK) ===
  const ForegroundService = {
    /**
     * Inicia serviço em segundo plano para playback de áudio
     */
    start: function(title, artist, imageUrl) {
      if (typeof Android !== 'undefined' && typeof Android.startService === 'function') {
        try {
          Android.startService(title || 'IPTV Player', artist || 'Reproduzindo', imageUrl || '');
          return true;
        } catch (e) {
          console.log('Foreground service não disponível');
        }
      }
      return false;
    },
    
    /**
     * Para serviço em segundo plano
     */
    stop: function() {
      if (typeof Android !== 'undefined' && typeof Android.stopService === 'function') {
        try {
          Android.stopService();
          return true;
        } catch (e) {}
      }
      return false;
    },
    
    /**
     * Atualiza notificação do serviço
     */
    updateNotification: function(title, artist, imageUrl) {
      if (typeof Android !== 'undefined' && typeof Android.updateNotification === 'function') {
        try {
          Android.updateNotification(title, artist, imageUrl || '');
          return true;
        } catch (e) {}
      }
      return false;
    }
  };

  // === INICIALIZAÇÃO ===
  function init() {
    // Aplica fastClick para mobile
    TouchCompat.fastClick();
    
    // Substitui método de fullscreen padrão
    if (typeof document.documentElement.requestFullscreen !== 'function') {
      document.documentElement.requestFullscreen = function() {
        return FullscreenCompat.requestFullscreen(this);
      };
    }
    
    // Log de ambiente
    console.log('WebView Compat inicializado');
    console.log('Android WebView:', WebViewCompat.isAndroidWebView());
    console.log('Sketchware:', WebViewCompat.isSketchware());
    console.log('Mobile:', WebViewCompat.isMobile());
    console.log('LocalStorage:', WebViewCompat.supportsLocalStorage());
  }

  // === EXPORTA PARA GLOBAL ===
  window.WebViewCompat = WebViewCompat;
  window.FullscreenCompat = FullscreenCompat;
  window.StorageCompat = StorageCompat;
  window.TouchCompat = TouchCompat;
  window.MediaCompat = MediaCompat;
  window.NavigationCompat = NavigationCompat;
  window.ForegroundService = ForegroundService;

  // Inicializa quando DOM estiver pronto
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
