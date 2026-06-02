import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "br.sosvision.defesacivil",
  appName: "SOS Defesa Civil",
  webDir: "dist",
  android: {
    // Exigido pelo plugin de background-geolocation (ver README do plugin).
    useLegacyBridge: true,
  },
};

export default config;
