const RELEASE_BASE =
  "https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/latest/download";

export const THORPE_DOWNLOADS = {
  releasesPage: "https://github.com/jonniethorpe45-max/Thorpe-Workforce/releases/latest",
  windowsExe: `${RELEASE_BASE}/Thorpe_1.0.0_x64-setup.exe`,
  windowsMsi: `${RELEASE_BASE}/Thorpe_1.0.0_x64_en-US.msi`,
  macosDmg: `${RELEASE_BASE}/Thorpe_1.0.0_aarch64.dmg`,
  linuxAppImage: `${RELEASE_BASE}/Thorpe_1.0.0_amd64.AppImage`,
  linuxDeb: `${RELEASE_BASE}/Thorpe_1.0.0_amd64.deb`,
} as const;
