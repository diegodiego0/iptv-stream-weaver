# IPTV Player v1.1.3 - Versão Modularizada

## 📁 Estrutura de Pastas

```
iptv-modular/
├── index.html              # HTML principal (estrutura apenas)
├── css/
│   └── styles.css          # Todos os estilos CSS
├── js/
│   ├── webview-compat.js   # Camada de compatibilidade Android WebView
│   └── app.js              # Lógica principal JavaScript
├── img/                    # Recursos de imagem (adicionar conforme necessário)
├── fonts/                  # Fontes personalizadas (adicionar conforme necessário)
└── README.md               # Este arquivo
```

## 🎯 Objetivo

Este projeto foi refatorado do arquivo HTML original `IPTV Player v1.1.3.html` para separar CSS, JavaScript e HTML em arquivos distintos, mantendo **100% da funcionalidade e aparência original**.

## ✅ O Que Foi Mantido (Sem Alterações)

- **Todos os IDs de elementos** - Mantidos exatamente iguais
- **Todas as classes CSS** - Nenhuma renomeada ou removida
- **Todas as funções JavaScript** - Mesmos nomes e comportamentos
- **Toda a estrutura HTML** - Mesma hierarquia de elementos
- **Todos os seletores** - CSS e JS usam os mesmos seletores
- **Layout e UI** - Aparência idêntica ao original
- **Fluxos de navegação** - Mesmo comportamento de interação

## 🆕 O Que Foi Adicionado

### Camada de Compatibilidade Android WebView (`webview-compat.js`)

Este arquivo adiciona suporte para execução em Android WebView sem modificar a lógica original:

#### 1. **FullscreenCompat** - Fullscreen com fallbacks
```javascript
// Solicitar fullscreen
FullscreenCompat.requestFullscreen(element);

// Sair do fullscreen
FullscreenCompat.exitFullscreen();

// Toggle fullscreen
FullscreenCompat.toggleFullscreen(element);

// Verificar se está em fullscreen
FullscreenCompat.isFullscreen();
```

#### 2. **StorageCompat** - Persistência de dados
```javascript
// Salvar dados
StorageCompat.setItem('chave', 'valor');

// Recuperar dados
const valor = StorageCompat.getItem('chave');

// Remover dados
StorageCompat.removeItem('chave');

// Limpar tudo
StorageCompat.clear();
```

#### 3. **TouchCompat** - Eventos de clique otimizados
```javascript
// Adicionar listener com suporte touch
TouchCompat.addClickListener(elemento, callback);

// Ativar fast click (remove delay de 300ms)
TouchCompat.fastClick();
```

#### 4. **MediaCompat** - Playback de mídia
```javascript
// Reproduzir mídia com handling de autoplay
MediaCompat.playMedia(videoElement);

// Pausar mídia
MediaCompat.pauseMedia(videoElement);

// Parar mídia
MediaCompat.stopMedia(videoElement);
```

#### 5. **NavigationCompat** - Navegação de links
```javascript
// Abrir link (interno ou externo)
NavigationCompat.openLink(url, target);

// Verificar se é link externo
NavigationCompat.isExternalLink(url);

// Voltar na navegação
NavigationCompat.goBack();
```

#### 6. **ForegroundService** - Background playback (Android)
```javascript
// Iniciar serviço em segundo plano
ForegroundService.start('Título', 'Artista', 'url-imagem');

// Parar serviço
ForegroundService.stop();

// Atualizar notificação
ForegroundService.updateNotification('Novo Título', 'Novo Artista');
```

## 📱 Compatibilidade

| Plataforma | Versão Mínima | Status |
|------------|---------------|--------|
| Android WebView | API 21 (5.0) | ✅ Completo |
| Sketchware | Padrão | ✅ Completo |
| Sketchware | Modificado | ✅ Completo |
| Chrome | 60+ | ✅ Completo |
| Firefox | 55+ | ✅ Completo |
| Safari | 11+ | ✅ Completo |
| Edge | 79+ | ✅ Completo |

## 🚀 Como Usar

### No Navegador Desktop

1. Abra `index.html` em qualquer navegador moderno
2. A aplicação funciona normalmente como no arquivo original

### No Android via Sketchware

1. Copie a pasta `iptv-modular/` para `android_asset/` do projeto
2. Configure o WebView para carregar `file:///android_asset/iptv-modular/index.html`
3. A camada de compatibilidade ativa automaticamente os recursos do Android

### Estrutura para `android_asset/`

```
android_asset/
└── iptv-modular/
    ├── index.html
    ├── css/
    │   └── styles.css
    └── js/
        ├── webview-compat.js
        └── app.js
```

## 🔧 Integração com Android Nativo (Opcional)

Para habilitar comunicação completa com Android, implemente a interface JavaScript no seu código Java:

```java
webView.addJavascriptInterface(new Object() {
    @JavascriptInterface
    public void startService(String title, String artist, String imageUrl) {
        // Iniciar Foreground Service
    }
    
    @JavascriptInterface
    public void stopService() {
        // Parar Foreground Service
    }
    
    @JavascriptInterface
    public String getStorage(String key) {
        // Recuperar do SharedPreferences
        return prefs.getString(key, null);
    }
    
    @JavascriptInterface
    public void setStorage(String key, String value) {
        // Salvar no SharedPreferences
        prefs.edit().putString(key, value).apply();
    }
    
    @JavascriptInterface
    public void requestFullscreen() {
        // Modo imersivo
    }
    
    @JavascriptInterface
    public void exitFullscreen() {
        // Sair do modo imersivo
    }
}, "Android");
```

## 📝 Notas Importantes

1. **Caminhos Relativos**: Todos os arquivos CSS e JS usam caminhos relativos (`./css/`, `./js/`) para compatibilidade com `file:///`

2. **CDNs Externos**: Bootstrap, Font Awesome, Video.js e HLS.js ainda são carregados de CDN. Para funcionamento 100% offline, faça download e inclua localmente.

3. **Fallbacks**: A camada de compatibilidade sempre verifica primeiro os recursos nativos do Android antes de usar fallbacks JavaScript.

4. **Sem Dependências Externas**: O `webview-compat.js` não requer nenhuma biblioteca externa.

## 📄 Licença

Projeto refatorado mantendo a estrutura e funcionalidade do original. Use conforme os termos da licença original.
