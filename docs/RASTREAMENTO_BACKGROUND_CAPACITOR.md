# Rastreamento de localização com a tela fechada (background)
## Guia técnico reutilizável — Capacitor + background-geolocation
### Com adaptações para o SOS Mulher (violência doméstica / feminicídio)

> **Documento portátil.** Escrito para ser copiado para qualquer projeto que precise
> rastrear o GPS da vítima mesmo com o app minimizado, a tela bloqueada ou o app fechado.
> Validado na prática no projeto SOS VISION · Defesa Civil (`sos-vision-defesa-civil/app-mobile/`).

---

## 0. Resposta direta (por que disseram que "não dava")

Você ouviu antes que **não dá para rastrear a vítima com a tela fechada**. Isso está
**correto — para web/PWA puro.** É uma barreira de plataforma, de propósito, por privacidade.

Mas existe a saída: **empacotar o mesmo app web num app nativo com o Capacitor**
(o nome é *Capacitor*, não "capacitador") e usar um **plugin de geolocalização em
background**. Aí sim: Android e iOS continuam transmitindo a localização com o app
minimizado e a tela bloqueada.

| Abordagem | Tela bloqueada / app minimizado | App encerrado (swiped) | Instalar app? |
|---|---|---|---|
| PWA / site (web puro) | ❌ não | ❌ não | não |
| **Capacitor + plugin community** | ✅ sim | ⚠️ parcial | sim |
| **Capacitor + plugin Transistorsoft** | ✅ sim | ✅ sim (headless) | sim |

---

## 1. Por que web puro não consegue (a explicação técnica)

- **Service Worker não tem acesso à Geolocation API.** Mesmo com *Periodic Background
  Sync*, o SW não lê GPS — no máximo acorda e fala com uma aba **já aberta**, em
  intervalos longos demais para emergência.
- **`navigator.geolocation.watchPosition()` só roda em foreground.** Ao fechar/minimizar
  a aba, o JavaScript é suspenso e o rastreamento para.
- **iOS Safari é ainda mais restrito** — não há background location para web. É o maior
  gap entre PWA e app nativo no iPhone.

Conclusão: para "tela fechada" é **obrigatório** sair do navegador e ir para o nativo.

---

## 2. A solução: Capacitor + plugin nativo

**Capacitor** (da Ionic) empacota seu app web (HTML/JS/React/Vue/o que for) dentro de um
app nativo Android/iOS e dá acesso a APIs nativas via plugins. Você **reaproveita ~100%
do código web** que já tem.

**Plugins de background-geolocation:**
- `@capacitor-community/background-geolocation` — **gratuito**. Cobre app em background e
  tela bloqueada. Bom ponto de partida.
- `@transistorsoft/capacitor-background-geolocation` — mais robusto (rastreia mesmo com o
  app encerrado, modo *headless*, auto-sync para servidor). Algumas features são pagas.
  **Recomendado para SOS Mulher**, onde perder o sinal pode custar uma vida.

**Como funciona por baixo:**
- **Android:** sobe um *foreground service* do tipo `location` com uma **notificação
  persistente** (obrigatória pelo Android) e continua emitindo posições em background.
- **iOS:** usa *background location updates* (`UIBackgroundModes: location`) com permissão
  "Sempre"; o sistema mostra o indicador de localização na barra de status.

---

## 3. Implementação passo a passo

### 3.1 Pré-requisitos (máquina de desenvolvimento)
- Node 20+
- **Android:** Android Studio + SDK (API 34+) + **JDK 17**
- **iOS:** Mac + Xcode (não há como compilar iOS no Windows)

### 3.2 Adicionar o Capacitor a um projeto web existente
```bash
npm install @capacitor/core @capacitor/cli
npx cap init "Nome do App" br.suaempresa.appseguro --web-dir=dist
npm install @capacitor/android
npm run build              # gera a pasta dist/
npx cap add android
```

### 3.3 Instalar o plugin
```bash
npm install @capacitor-community/background-geolocation
npx cap sync
```

### 3.4 Configurar `capacitor.config.ts`
```ts
import type { CapacitorConfig } from "@capacitor/cli";
const config: CapacitorConfig = {
  appId: "br.suaempresa.appseguro",
  appName: "Nome do App",
  webDir: "dist",
  android: { useLegacyBridge: true },   // exigido pelo plugin
};
export default config;
```

### 3.5 Código (uma vez só, roda nas duas plataformas)
```ts
import { Capacitor, registerPlugin } from "@capacitor/core";
import type { BackgroundGeolocationPlugin } from "@capacitor-community/background-geolocation";

const BackgroundGeolocation =
  registerPlugin<BackgroundGeolocationPlugin>("BackgroundGeolocation");

let watcherId: string | null = null;

async function iniciarRastreamento(token: string, apiBase: string) {
  watcherId = await BackgroundGeolocation.addWatcher(
    {
      // ⚠️ SOS MULHER: este texto aparece na notificação do Android — leia a seção 4!
      backgroundMessage: "Sincronizando…",
      backgroundTitle: "App",
      requestPermissions: true,
      stale: false,
      distanceFilter: 10,            // metros entre atualizações
    },
    (location, error) => {
      if (error) {
        // ex.: usuária ainda não concedeu permissão "Sempre"
        if (error.code === "NOT_AUTHORIZED") BackgroundGeolocation.openSettings();
        return;
      }
      if (!location) return;
      // Envia ao backend (mesma API do seu rastreamento web)
      fetch(`${apiBase}/track/${token}/ponto`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lat: location.latitude,
          lng: location.longitude,
          acuracia_m: location.accuracy,
          fonte: "gps",
        }),
      }).catch(() => { /* TODO: bufferizar offline e reenviar */ });
    }
  );
}

async function pararRastreamento() {
  if (watcherId) {
    await BackgroundGeolocation.removeWatcher({ id: watcherId });
    watcherId = null;
  }
}
```

### 3.6 Permissões Android — `android/app/src/main/AndroidManifest.xml`
O plugin já injeta `ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`, `FOREGROUND_SERVICE`,
`FOREGROUND_SERVICE_LOCATION` e `POST_NOTIFICATIONS`. **Falta adicionar a do background:**
```xml
<uses-permission android:name="android.permission.ACCESS_BACKGROUND_LOCATION" />
```
> No Android 11+ a permissão "Permitir o tempo todo" é concedida em **etapas**: o app pede
> "durante o uso" e depois a usuária precisa ir nas configurações e mudar para "Sempre".
> Faça uma tela explicando isso antes de pedir.

### 3.7 Permissões iOS — `ios/App/App/Info.plist`
```xml
<key>NSLocationWhenInUseUsageDescription</key>
<string>Para te localizar em caso de emergência.</string>
<key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
<string>Para te proteger mesmo com o celular bloqueado.</string>
<key>UIBackgroundModes</key>
<array><string>location</string></array>
```

### 3.8 Compilar e rodar
```bash
npm run build
npx cap sync
npx cap open android        # abre no Android Studio → Run num device real
# ou: cd android && ./gradlew assembleDebug
```
> Teste sempre em **device físico** (emulador não simula bem GPS/background).

---

## 4. ⚠️ CRÍTICO no SOS Mulher: discrição pode salvar (ou custar) a vida

Esta é a **maior diferença** entre Defesa Civil e SOS Mulher. Na enchente, uma notificação
"Rastreamento ativo" é ótima — tranquiliza a vítima. **Na violência doméstica, essa mesma
notificação na frente do agressor é uma sentença.**

O Android **obriga** o foreground service a exibir uma notificação persistente. Você não
pode removê-la, mas **pode disfarçá-la**. Estratégias:

1. **Notificação camuflada e genérica.** Nunca escreva "SOS", "rastreando", "polícia".
   Use algo invisível socialmente: `backgroundTitle: "Sistema"`,
   `backgroundMessage: "Sincronizando"` — ou o nome de um app banal (atualização, backup).
2. **Nome e ícone do app disfarçados.** Apps anti-violência famosos se passam por
   calculadora, app de notícias, rádio, receitas. O `appName` e o ícone do Capacitor
   devem refletir o disfarce, não a função real.
3. **iOS mostra o indicador de localização** (seta/“•” na barra de status) quando rastreia
   — também é visível. Não há como ocultar no iOS; documente o risco para a usuária.
4. **Acionamento discreto, rastreamento sob demanda.** Diferente da Defesa Civil (proativo),
   no SOS Mulher o ideal é o rastreamento **ligar só no momento do SOS** (palavra-código,
   botão escondido, toque triплo no botão de volume), não 24/7 — minimiza exposição,
   bateria e a chance de o agressor notar.
5. **Transistorsoft** permite controle fino da notificação (texto, ícone, prioridade
   baixa para ficar discreta) — outra razão para preferi-lo aqui.

> Regra de ouro: no SOS Mulher, **toda decisão de UX é decisão de segurança física.**
> Teste cada tela imaginando o agressor olhando por cima do ombro.

---

## 5. Limitações e armadilhas honestas

- **App encerrado/deslizado para fora:** o plugin *community* não garante; use o
  **Transistorsoft** (`stopOnTerminate: false`, headless) se isso for requisito — e no
  SOS Mulher, **é** requisito.
- **Bateria:** rastreamento contínuo consome. `distanceFilter` e rastreamento sob demanda
  ajudam.
- **Aprovação na Google Play:** apps que usam `ACCESS_BACKGROUND_LOCATION` passam por
  **revisão manual rigorosa** do Google — exigem justificativa, vídeo demonstrando o uso e
  política de privacidade clara. Apps de segurança pessoal são uma categoria aceita, mas
  **reserve semanas** para a aprovação. Na App Store, o uso de background location também é
  auditado.
- **Permissão "Sempre":** muitas usuárias negam por medo/desconhecimento — invista na tela
  de explicação e tenha um fallback (rastreamento só em foreground) para quem não conceder.
- **Buffer offline:** o exemplo acima não bufferiza. Em zonas sem sinal, guarde os pontos
  localmente (ex.: `localStorage`/SQLite) e reenvie ao reconectar.

---

## 6. Checklist de adaptação para o SEU projeto (SOS Mulher)

- [ ] Já tenho um app web/PWA com a UI da vítima e uma API `/track/{token}/ponto`? (reaproveita tudo)
- [ ] `npx cap init` + `cap add android` no projeto
- [ ] Instalar plugin (avaliar Transistorsoft pelo "app encerrado")
- [ ] `ACCESS_BACKGROUND_LOCATION` no manifesto + Info.plist no iOS
- [ ] **Notificação camuflada** (texto genérico) — seção 4
- [ ] **Nome/ícone do app disfarçados**
- [ ] Acionamento discreto liga o rastreamento **sob demanda**
- [ ] Tela de educação para a permissão "Sempre"
- [ ] Buffer offline + reenvio
- [ ] Endpoint backend que cria/recupera a sessão de rastreamento (ex.: `/track/ativar`)
- [ ] Política de privacidade + material para a revisão da Google Play

---

## 7. Código de referência pronto

Há uma implementação **funcionando** em `sos-vision-defesa-civil/app-mobile/`
(projeto SOS VISION · Defesa Civil), que você pode usar de molde:
- `src/main.ts` — lógica de `addWatcher` + fallback web + ativação de sessão
- `capacitor.config.ts` — config com `useLegacyBridge`
- `android/app/src/main/AndroidManifest.xml` — permissões
- `README.md` — passo a passo de build
- Backend: endpoint `POST /track/ativar` (cria/recupera sessão e devolve o token)

**Para o SOS Mulher, copie a estrutura e aplique a seção 4 (discrição) por cima.**

---

*Fontes: [MDN — Offline & background](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Offline_and_background_operation),
[MDN — Periodic Background Sync](https://developer.mozilla.org/en-US/docs/Web/API/Web_Periodic_Background_Synchronization_API),
[capacitor-community/background-geolocation](https://github.com/capacitor-community/background-geolocation),
[Transistorsoft Capacitor plugin](https://github.com/transistorsoft/capacitor-background-geolocation).*
