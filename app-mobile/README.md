# SOS VISION Mobile — Camada B (rastreamento com app fechado)

App nativo (Capacitor) que resolve a barreira investigada no §13 do `../../DEFESA_CIVIL_RS.md`:
**rastrear o GPS mesmo com o app em background / tela bloqueada** — o que o PWA puro
não consegue. Reusa a mesma API do backend (`/track/ativar` + `/track/{token}/ponto`).

Destinado à **camada B**: oferecido a vulneráveis pré-cadastrados (acamado, O₂, idoso só)
que aceitam instalar o app e dar permissão de localização "o tempo todo".

## Como funciona

- **Nativo (Android/iOS):** usa `@capacitor-community/background-geolocation`
  (`addWatcher`), que sobe um *foreground service* com notificação persistente e
  continua transmitindo com o app minimizado e a tela bloqueada.
- **Navegador (dev):** detecta via `Capacitor.isNativePlatform()` e cai para
  `navigator.geolocation.watchPosition` (só com a aba aberta).

Código único em `src/main.ts`.

## Rodar no navegador (validação rápida, sem background real)

```powershell
npm install
npm run dev          # http://localhost:5190
```
No campo "Servidor" use `http://localhost:8000` (backend já rodando via docker compose).
Telefone de demo: `5551988887777` (Dona Alzira). Clique **ATIVAR PROTEÇÃO** → o app
chama `/track/ativar`, recebe o token e começa a transmitir (a posição aparece na Sala).

## Compilar o APK Android (na máquina de desenvolvimento)

Pré-requisitos (NÃO incluídos neste ambiente):
- **Android Studio** + **Android SDK** (API 34+)
- **JDK 17**
- Variáveis `ANDROID_HOME` / `JAVA_HOME` configuradas

```powershell
npm install
npm run build            # gera dist/
npx cap sync android     # copia web + plugins p/ o projeto nativo
npx cap open android     # abre no Android Studio → Run no device/emulador
# ou, por linha de comando:
cd android ; ./gradlew assembleDebug   # APK em android/app/build/outputs/apk/debug/
```

O projeto Android já foi gerado (`npx cap add android`) e o plugin detectado
(`background-geolocation@1.2.26`). A permissão **`ACCESS_BACKGROUND_LOCATION`** já foi
adicionada ao `android/app/src/main/AndroidManifest.xml` (as demais vêm do plugin).

> No emulador, o backend local fica em `http://10.0.2.2:8000` (não `localhost`).

## iOS (exige Mac + Xcode)

```bash
npm run build && npx cap add ios && npx cap sync ios && npx cap open ios
```
Adicionar ao `ios/App/App/Info.plist`:
```xml
<key>NSLocationWhenInUseUsageDescription</key>
<string>A Defesa Civil precisa da sua localização para te resgatar.</string>
<key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
<string>Para te proteger mesmo com o celular bloqueado.</string>
<key>UIBackgroundModes</key>
<array><string>location</string></array>
```

## Limitação honesta (escolha do plugin)

`@capacitor-community/background-geolocation` (gratuito) garante rastreamento com o app
**em background e tela bloqueada** — cobre o caso real "minimizei / bloqueei o celular".
Para rastreamento garantido mesmo com o app **encerrado/deslizado para fora** (headless,
`stopOnTerminate:false`), o plugin **`@transistorsoft/capacitor-background-geolocation`**
é mais robusto (algumas features são pagas). Trocar é direto: mesma ideia de `addWatcher`.

Para Defesa Civil, o ganho sobre o PWA já é enorme: o PWA para de rastrear ao minimizar;
este app continua com a tela bloqueada — que é exatamente o "fechei a tela" do usuário.
