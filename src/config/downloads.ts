import { THORPE_VERSION } from "./version";

const RELEASE_BASE =
  "https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/latest/download";

export const THORPE_DOWNLOADS = {
  releasesPage: "https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/latest",
  windowsExe: `${RELEASE_BASE}/Thorpe_${THORPE_VERSION}_x64-setup.exe`,
  windowsMsi: `${RELEASE_BASE}/Thorpe_${THORPE_VERSION}_x64_en-US.msi`,
  macosDmg: `${RELEASE_BASE}/Thorpe_${THORPE_VERSION}_aarch64.dmg`,
  linuxAppImage: `${RELEASE_BASE}/Thorpe_${THORPE_VERSION}_amd64.AppImage`,
  linuxDeb: `${RELEASE_BASE}/Thorpe_${THORPE_VERSION}_amd64.deb`,
} as const;
