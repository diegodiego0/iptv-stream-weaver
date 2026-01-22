# Implementação de Foreground Service para IPTV Player v1.1.3

## Visão Geral

Esta documentação fornece código Java completo e pronto para copiar e colar no Sketchware, implementando suporte real para execução em segundo plano no Android moderno (API 26+).

---

## 1. MainActivity.java - Código Completo

```java
// ===============================================
// MAINACTIVITY.JAVA - CÓDIGO COMPLETO PARA SKETCHWARE
// ===============================================
// Cole este código no evento onCreate da MainActivity

import android.app.Activity;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;

public class MainActivity extends Activity {
    
    private WebView webView;
    private View customView;
    private WebChromeClient.CustomViewCallback customViewCallback;
    private FrameLayout fullscreenContainer;
    private int originalSystemUiVisibility;
    
    // Constantes do Notification Channel
    public static final String CHANNEL_ID = "iptv_foreground_channel";
    public static final String CHANNEL_NAME = "IPTV Player em Segundo Plano";
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // Cria Notification Channel para Android 8+
        createNotificationChannel();
        
        // Layout principal
        FrameLayout mainLayout = new FrameLayout(this);
        mainLayout.setLayoutParams(new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT, 
            FrameLayout.LayoutParams.MATCH_PARENT
        ));
        
        // Container para fullscreen
        fullscreenContainer = new FrameLayout(this);
        fullscreenContainer.setLayoutParams(new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT, 
            FrameLayout.LayoutParams.MATCH_PARENT
        ));
        fullscreenContainer.setBackgroundColor(0xFF000000);
        fullscreenContainer.setVisibility(View.GONE);
        
        // Configuração do WebView
        webView = new WebView(this);
        webView.setLayoutParams(new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT, 
            FrameLayout.LayoutParams.MATCH_PARENT
        ));
        
        // Configurações avançadas do WebView
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setLoadsImagesAutomatically(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(true);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        
        // Adiciona interface JavaScript ↔ Android
        webView.addJavascriptInterface(new AndroidBridge(this), "Android");
        
        // WebViewClient básico
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return false;
            }
        });
        
        // WebChromeClient com suporte a Fullscreen
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onShowCustomView(View view, CustomViewCallback callback) {
                if (customView != null) {
                    callback.onCustomViewHidden();
                    return;
                }
                
                customView = view;
                customViewCallback = callback;
                
                // Salva estado atual da UI
                originalSystemUiVisibility = getWindow().getDecorView().getSystemUiVisibility();
                
                // Modo imersivo fullscreen
                getWindow().getDecorView().setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                    | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                    | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                    | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                    | View.SYSTEM_UI_FLAG_FULLSCREEN
                    | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                );
                
                // Mantém tela ligada
                getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
                
                // Mostra view customizada
                fullscreenContainer.addView(view);
                fullscreenContainer.setVisibility(View.VISIBLE);
                webView.setVisibility(View.GONE);
            }
            
            @Override
            public void onHideCustomView() {
                if (customView == null) {
                    return;
                }
                
                // Remove view customizada
                fullscreenContainer.removeView(customView);
                fullscreenContainer.setVisibility(View.GONE);
                webView.setVisibility(View.VISIBLE);
                
                // Restaura UI original
                getWindow().getDecorView().setSystemUiVisibility(originalSystemUiVisibility);
                getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
                
                // Callback
                if (customViewCallback != null) {
                    customViewCallback.onCustomViewHidden();
                }
                
                customView = null;
                customViewCallback = null;
            }
        });
        
        // Monta layout
        mainLayout.addView(webView);
        mainLayout.addView(fullscreenContainer);
        setContentView(mainLayout);
        
        // Carrega o HTML
        webView.loadUrl("file:///android_asset/index.html");
    }
    
    /**
     * Cria Notification Channel para Android 8+ (API 26+)
     */
    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                CHANNEL_NAME,
                NotificationManager.IMPORTANCE_LOW
            );
            channel.setDescription("Mantém o player rodando em segundo plano");
            channel.setShowBadge(false);
            channel.enableLights(false);
            channel.enableVibration(false);
            
            NotificationManager manager = getSystemService(NotificationManager.class);
            if (manager != null) {
                manager.createNotificationChannel(channel);
            }
        }
    }
    
    @Override
    public void onBackPressed() {
        // Sai do fullscreen primeiro
        if (customView != null) {
            webView.getWebChromeClient().onHideCustomView();
            return;
        }
        
        // Volta no histórico do WebView
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (webView != null) {
            webView.destroy();
        }
    }
    
    /**
     * Classe interna - Ponte JavaScript ↔ Android
     */
    public class AndroidBridge {
        private Context context;
        
        public AndroidBridge(Context context) {
            this.context = context;
        }
        
        /**
         * Inicia o Foreground Service
         * Chamado via JavaScript: Android.startService()
         */
        @JavascriptInterface
        public void startService() {
            Intent serviceIntent = new Intent(context, IPTVForegroundService.class);
            serviceIntent.setAction("START_SERVICE");
            
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(serviceIntent);
            } else {
                context.startService(serviceIntent);
            }
        }
        
        /**
         * Para o Foreground Service
         * Chamado via JavaScript: Android.stopService()
         */
        @JavascriptInterface
        public void stopService() {
            Intent serviceIntent = new Intent(context, IPTVForegroundService.class);
            serviceIntent.setAction("STOP_SERVICE");
            context.startService(serviceIntent);
        }
        
        /**
         * Atualiza informações na notificação
         * Chamado via JavaScript: Android.updateNotification("Título", "Descrição")
         */
        @JavascriptInterface
        public void updateNotification(String title, String description) {
            Intent serviceIntent = new Intent(context, IPTVForegroundService.class);
            serviceIntent.setAction("UPDATE_NOTIFICATION");
            serviceIntent.putExtra("title", title);
            serviceIntent.putExtra("description", description);
            context.startService(serviceIntent);
        }
        
        /**
         * Verifica se o serviço está rodando
         * Chamado via JavaScript: Android.isServiceRunning()
         */
        @JavascriptInterface
        public boolean isServiceRunning() {
            return IPTVForegroundService.isRunning;
        }
        
        /**
         * Mantém a tela ligada
         * Chamado via JavaScript: Android.keepScreenOn(true/false)
         */
        @JavascriptInterface
        public void keepScreenOn(final boolean keepOn) {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    if (keepOn) {
                        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
                    } else {
                        getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
                    }
                }
            });
        }
        
        /**
         * Mostra um Toast nativo
         * Chamado via JavaScript: Android.showToast("Mensagem")
         */
        @JavascriptInterface
        public void showToast(final String message) {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    android.widget.Toast.makeText(context, message, android.widget.Toast.LENGTH_SHORT).show();
                }
            });
        }
        
        /**
         * Obtém versão do Android
         * Chamado via JavaScript: Android.getAndroidVersion()
         */
        @JavascriptInterface
        public int getAndroidVersion() {
            return Build.VERSION.SDK_INT;
        }
    }
}
```

---

## 2. IPTVForegroundService.java - Código Completo

```java
// ===============================================
// IPTVFOREGROUNDSERVICE.JAVA - CÓDIGO COMPLETO
// ===============================================
// Crie uma nova classe Java no Sketchware com este código

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;

public class IPTVForegroundService extends Service {
    
    public static final String CHANNEL_ID = "iptv_foreground_channel";
    public static final int NOTIFICATION_ID = 1001;
    
    // Flag estática para verificar se o serviço está rodando
    public static boolean isRunning = false;
    
    private String currentTitle = "IPTV Player";
    private String currentDescription = "Reproduzindo em segundo plano";
    
    @Override
    public void onCreate() {
        super.onCreate();
        isRunning = true;
    }
    
    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null) {
            String action = intent.getAction();
            
            if ("START_SERVICE".equals(action)) {
                startForegroundServiceWithNotification();
            } else if ("STOP_SERVICE".equals(action)) {
                stopForegroundService();
            } else if ("UPDATE_NOTIFICATION".equals(action)) {
                String title = intent.getStringExtra("title");
                String description = intent.getStringExtra("description");
                
                if (title != null) currentTitle = title;
                if (description != null) currentDescription = description;
                
                updateNotification();
            }
        }
        
        return START_STICKY;
    }
    
    /**
     * Inicia o serviço em primeiro plano com notificação persistente
     */
    private void startForegroundServiceWithNotification() {
        // Cria canal de notificação para Android 8+
        createNotificationChannel();
        
        // Cria notificação
        Notification notification = buildNotification(currentTitle, currentDescription);
        
        // Inicia em foreground
        startForeground(NOTIFICATION_ID, notification);
        
        isRunning = true;
    }
    
    /**
     * Para o serviço
     */
    private void stopForegroundService() {
        isRunning = false;
        stopForeground(true);
        stopSelf();
    }
    
    /**
     * Atualiza a notificação com novas informações
     */
    private void updateNotification() {
        if (isRunning) {
            Notification notification = buildNotification(currentTitle, currentDescription);
            NotificationManager manager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
            if (manager != null) {
                manager.notify(NOTIFICATION_ID, notification);
            }
        }
    }
    
    /**
     * Cria Notification Channel para Android 8+ (API 26+)
     */
    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                "IPTV Player em Segundo Plano",
                NotificationManager.IMPORTANCE_LOW
            );
            channel.setDescription("Mantém o player IPTV rodando em segundo plano");
            channel.setShowBadge(false);
            channel.enableLights(false);
            channel.enableVibration(false);
            channel.setSound(null, null);
            
            NotificationManager manager = getSystemService(NotificationManager.class);
            if (manager != null) {
                manager.createNotificationChannel(channel);
            }
        }
    }
    
    /**
     * Constrói a notificação persistente
     */
    private Notification buildNotification(String title, String description) {
        // Intent para abrir o app ao clicar na notificação
        Intent notificationIntent = new Intent(this, MainActivity.class);
        notificationIntent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        
        int pendingIntentFlags = PendingIntent.FLAG_UPDATE_CURRENT;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            pendingIntentFlags |= PendingIntent.FLAG_IMMUTABLE;
        }
        
        PendingIntent pendingIntent = PendingIntent.getActivity(
            this, 
            0, 
            notificationIntent, 
            pendingIntentFlags
        );
        
        // Intent para ação de parar
        Intent stopIntent = new Intent(this, IPTVForegroundService.class);
        stopIntent.setAction("STOP_SERVICE");
        PendingIntent stopPendingIntent = PendingIntent.getService(
            this, 
            1, 
            stopIntent, 
            pendingIntentFlags
        );
        
        // Constrói a notificação
        Notification.Builder builder;
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            builder = new Notification.Builder(this, CHANNEL_ID);
        } else {
            builder = new Notification.Builder(this);
            builder.setPriority(Notification.PRIORITY_LOW);
        }
        
        builder.setContentTitle(title)
               .setContentText(description)
               .setSmallIcon(android.R.drawable.ic_media_play)
               .setContentIntent(pendingIntent)
               .setOngoing(true)
               .setAutoCancel(false);
        
        // Adiciona ação de parar
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT_WATCH) {
            Notification.Action stopAction = new Notification.Action.Builder(
                android.R.drawable.ic_media_pause,
                "Parar",
                stopPendingIntent
            ).build();
            builder.addAction(stopAction);
        }
        
        return builder.build();
    }
    
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
    
    @Override
    public void onDestroy() {
        super.onDestroy();
        isRunning = false;
    }
    
    @Override
    public void onTaskRemoved(Intent rootIntent) {
        // O serviço continua rodando mesmo se o app for removido das recentes
        super.onTaskRemoved(rootIntent);
    }
}
```

---

## 3. AndroidManifest.xml - Configuração Completa

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="seu.pacote.aqui">

    <!-- Permissões necessárias -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    
    <!-- Para Android 13+ (API 33+) -->
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    
    <!-- Para Android 14+ (API 34+) - tipo específico de foreground service -->
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="IPTV Player"
        android:usesCleartextTraffic="true"
        android:networkSecurityConfig="@xml/network_security_config"
        android:hardwareAccelerated="true">
        
        <!-- MainActivity -->
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|keyboardHidden"
            android:screenOrientation="sensor"
            android:theme="@android:style/Theme.NoTitleBar.Fullscreen"
            android:launchMode="singleTask">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
        
        <!-- Foreground Service -->
        <service
            android:name=".IPTVForegroundService"
            android:enabled="true"
            android:exported="false"
            android:foregroundServiceType="mediaPlayback" />
            
    </application>

</manifest>
```

---

## 4. network_security_config.xml

Crie este arquivo em `res/xml/network_security_config.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <base-config cleartextTrafficPermitted="true">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>
</network-security-config>
```

---

## 5. Trechos JavaScript para o HTML

Adicione este código JavaScript **no final do arquivo HTML, antes de `</body>`**, sem alterar nenhum código existente:

```html
<!-- =============================================== -->
<!-- BRIDGE ANDROID - ADICIONAR ANTES DE </body> -->
<!-- =============================================== -->
<script>
// ============================================
// ANDROID BRIDGE - Comunicação JavaScript ↔ Android
// ============================================

/**
 * Objeto AndroidBridge - Interface para comunicação com Android nativo
 * Funciona apenas dentro do WebView Android
 * No navegador, as funções falham silenciosamente
 */
window.AndroidBridge = {
    
    /**
     * Verifica se está rodando no Android WebView
     */
    isAndroid: function() {
        return typeof Android !== 'undefined';
    },
    
    /**
     * Inicia o Foreground Service para reprodução em segundo plano
     */
    startBackgroundService: function() {
        if (this.isAndroid()) {
            try {
                Android.startService();
                console.log('[AndroidBridge] Serviço em segundo plano iniciado');
                return true;
            } catch (e) {
                console.error('[AndroidBridge] Erro ao iniciar serviço:', e);
                return false;
            }
        }
        console.log('[AndroidBridge] Não está no Android, serviço não iniciado');
        return false;
    },
    
    /**
     * Para o Foreground Service
     */
    stopBackgroundService: function() {
        if (this.isAndroid()) {
            try {
                Android.stopService();
                console.log('[AndroidBridge] Serviço em segundo plano parado');
                return true;
            } catch (e) {
                console.error('[AndroidBridge] Erro ao parar serviço:', e);
                return false;
            }
        }
        return false;
    },
    
    /**
     * Atualiza as informações exibidas na notificação
     * @param {string} title - Título da notificação
     * @param {string} description - Descrição/subtítulo
     */
    updateNotification: function(title, description) {
        if (this.isAndroid()) {
            try {
                Android.updateNotification(title, description);
                console.log('[AndroidBridge] Notificação atualizada:', title);
                return true;
            } catch (e) {
                console.error('[AndroidBridge] Erro ao atualizar notificação:', e);
                return false;
            }
        }
        return false;
    },
    
    /**
     * Verifica se o serviço está rodando
     */
    isServiceRunning: function() {
        if (this.isAndroid()) {
            try {
                return Android.isServiceRunning();
            } catch (e) {
                return false;
            }
        }
        return false;
    },
    
    /**
     * Mantém a tela ligada durante a reprodução
     * @param {boolean} keepOn - true para manter ligada, false para desativar
     */
    keepScreenOn: function(keepOn) {
        if (this.isAndroid()) {
            try {
                Android.keepScreenOn(keepOn);
                return true;
            } catch (e) {
                return false;
            }
        }
        return false;
    },
    
    /**
     * Mostra um Toast nativo do Android
     * @param {string} message - Mensagem a exibir
     */
    showToast: function(message) {
        if (this.isAndroid()) {
            try {
                Android.showToast(message);
                return true;
            } catch (e) {
                return false;
            }
        }
        // Fallback para navegador - não faz nada ou usa alert
        console.log('[AndroidBridge] Toast (browser fallback):', message);
        return false;
    },
    
    /**
     * Obtém a versão da API Android
     */
    getAndroidVersion: function() {
        if (this.isAndroid()) {
            try {
                return Android.getAndroidVersion();
            } catch (e) {
                return 0;
            }
        }
        return 0;
    }
};

// ============================================
// INTEGRAÇÃO AUTOMÁTICA COM O PLAYER
// ============================================

/**
 * Hook automático para iniciar/parar serviço baseado na reprodução
 * Adiciona listeners ao player existente sem modificar código original
 */
(function initAndroidIntegration() {
    
    // Aguarda o player estar pronto
    function waitForPlayer() {
        // Verifica se o player video.js existe
        if (typeof videojs !== 'undefined' && document.getElementById('videoPlayer')) {
            const player = videojs('videoPlayer');
            
            // Quando começa a reproduzir
            player.on('play', function() {
                if (AndroidBridge.isAndroid()) {
                    AndroidBridge.startBackgroundService();
                    AndroidBridge.keepScreenOn(true);
                    
                    // Tenta obter info do que está tocando
                    const currentItem = window.currentPlayingItem || {};
                    const title = currentItem.name || 'IPTV Player';
                    const type = currentItem.type || 'Reproduzindo';
                    AndroidBridge.updateNotification(title, type + ' em segundo plano');
                }
            });
            
            // Quando pausa
            player.on('pause', function() {
                // Mantém o serviço rodando mas atualiza a notificação
                if (AndroidBridge.isAndroid()) {
                    const currentItem = window.currentPlayingItem || {};
                    const title = currentItem.name || 'IPTV Player';
                    AndroidBridge.updateNotification(title, 'Pausado');
                }
            });
            
            // Quando termina
            player.on('ended', function() {
                if (AndroidBridge.isAndroid()) {
                    AndroidBridge.stopBackgroundService();
                    AndroidBridge.keepScreenOn(false);
                }
            });
            
            // Quando ocorre erro
            player.on('error', function() {
                if (AndroidBridge.isAndroid()) {
                    AndroidBridge.updateNotification('IPTV Player', 'Erro na reprodução');
                }
            });
            
            console.log('[AndroidBridge] Integração com player configurada');
            
        } else {
            // Tenta novamente em 500ms
            setTimeout(waitForPlayer, 500);
        }
    }
    
    // Inicia quando o DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', waitForPlayer);
    } else {
        waitForPlayer();
    }
    
})();

// ============================================
// HELPER GLOBAL PARA ATUALIZAR ITEM ATUAL
// ============================================

/**
 * Chame esta função ao trocar de canal/filme/série/rádio
 * Ex: setCurrentPlayingItem({ name: 'Globo', type: 'Canal' });
 */
window.setCurrentPlayingItem = function(item) {
    window.currentPlayingItem = item;
    
    if (AndroidBridge.isAndroid() && AndroidBridge.isServiceRunning()) {
        const title = item.name || 'IPTV Player';
        const desc = (item.type || 'Reproduzindo') + ' em segundo plano';
        AndroidBridge.updateNotification(title, desc);
    }
};

console.log('[AndroidBridge] Bridge JavaScript carregada com sucesso');
</script>
```

---

## 6. Como Integrar no Código Existente (Opcional)

Se quiser atualizar automaticamente a notificação quando um item começa a tocar, adicione estas linhas dentro das funções de reprodução existentes (sem modificar nada mais):

### No método `playChannel`:
```javascript
// Adicione NO INÍCIO da função playChannel, após os parâmetros
window.setCurrentPlayingItem({ name: channel.name, type: 'Canal' });
```

### No método `playMovie`:
```javascript
// Adicione NO INÍCIO da função playMovie
window.setCurrentPlayingItem({ name: movie.name, type: 'Filme' });
```

### No método `playRadio`:
```javascript
// Adicione NO INÍCIO da função playRadio
window.setCurrentPlayingItem({ name: radio.name, type: 'Rádio' });
```

### No método `playEpisode`:
```javascript
// Adicione NO INÍCIO da função playEpisode
window.setCurrentPlayingItem({ name: episode.title || episode.name, type: 'Série' });
```

---

## 7. Instruções para Sketchware

### Passo 1: MainActivity
1. Copie todo o código da seção 1 (MainActivity.java)
2. No Sketchware, cole no bloco `onCreate` da sua Activity principal
3. Ajuste imports conforme necessário

### Passo 2: Foreground Service
1. Crie uma nova classe Java chamada `IPTVForegroundService`
2. Cole todo o código da seção 2
3. Certifique-se de que o nome da classe corresponde ao registrado no Manifest

### Passo 3: AndroidManifest
1. Adicione as permissões listadas na seção 3
2. Registre o Service dentro da tag `<application>`
3. Adicione `android:foregroundServiceType="mediaPlayback"` ao Service

### Passo 4: HTML
1. Abra seu arquivo `index.html`
2. Vá até o final, antes de `</body>`
3. Cole todo o bloco JavaScript da seção 5
4. Salve o arquivo

---

## 8. Testando

1. **Compile o app** no Sketchware
2. **Instale** no dispositivo Android
3. **Abra o app** e inicie um canal/rádio
4. **Minimize o app** ou pressione Home
5. **Verifique** se aparece a notificação persistente
6. **O áudio deve continuar** mesmo com a tela desligada

---

## 9. Compatibilidade

| Android Version | API Level | Suporte |
|-----------------|-----------|---------|
| Android 5.0-5.1 | 21-22 | ✅ Funciona |
| Android 6.0 | 23 | ✅ Funciona |
| Android 7.0-7.1 | 24-25 | ✅ Funciona |
| Android 8.0-8.1 | 26-27 | ✅ Funciona (requer Notification Channel) |
| Android 9 | 28 | ✅ Funciona |
| Android 10 | 29 | ✅ Funciona |
| Android 11 | 30 | ✅ Funciona |
| Android 12 | 31-32 | ✅ Funciona |
| Android 13 | 33 | ✅ Funciona (requer permissão POST_NOTIFICATIONS) |
| Android 14+ | 34+ | ✅ Funciona (requer foregroundServiceType) |

---

## 10. Solução de Problemas

### Notificação não aparece
- Verifique se o Notification Channel foi criado
- Certifique-se de que as permissões estão no Manifest
- No Android 13+, solicite permissão POST_NOTIFICATIONS

### Serviço é encerrado
- Verifique se `startForeground()` está sendo chamado
- Confirme que a notificação tem `setOngoing(true)`
- Alguns fabricantes (Xiaomi, Huawei) têm gerenciadores agressivos de bateria

### Áudio para quando minimiza
- Certifique-se de que `mediaPlaybackRequiresUserGesture` está `false`
- O Foreground Service deve estar ativo antes de minimizar

---

**Arquivo gerado para: IPTV Player v1.1.3.html**
**Data: Janeiro 2025**
**Compatível com: Sketchware e Sketchware Pro**
