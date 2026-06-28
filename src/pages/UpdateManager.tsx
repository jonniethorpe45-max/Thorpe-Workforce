import { useEffect, useState } from "react";
import { Download, CheckCircle, RefreshCw, ExternalLink } from "lucide-react";
import { THORPE_DOWNLOADS } from "../config/downloads";
import { thorpeApi } from "../services/tauri";
import type { UpdateInfo } from "../services/types";

const PLATFORM_DOWNLOADS = [
  { label: "Windows (.exe)", href: THORPE_DOWNLOADS.windowsExe },
  { label: "Windows (.msi)", href: THORPE_DOWNLOADS.windowsMsi },
  { label: "macOS Apple Silicon (.dmg)", href: THORPE_DOWNLOADS.macosDmg },
  { label: "Linux (.AppImage)", href: THORPE_DOWNLOADS.linuxAppImage },
  { label: "Linux (.deb)", href: THORPE_DOWNLOADS.linuxDeb },
];

export function UpdateManager() {
  const [updateInfo, setUpdateInfo] = useState<UpdateInfo | null>(null);
  const [checking, setChecking] = useState(false);

  const openUrl = async (url: string) => {
    try {
      await thorpeApi.openExternalUrl(url);
    } catch (err) {
      console.error(err);
      window.open(url, "_blank", "noopener,noreferrer");
    }
  };

  const checkUpdates = async () => {
    setChecking(true);
    try {
      const info = await thorpeApi.checkForUpdates();
      setUpdateInfo(info);
    } catch (err) {
      console.error(err);
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    checkUpdates();
  }, []);

  return (
    <div className="mx-auto max-w-2xl space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Update Manager</h1>
        <p className="mt-1 text-gray-400">Keep Thorpe up to date with the latest features and security fixes.</p>
      </div>

      <div className="card space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Download className="h-6 w-6 text-thorpe-400" />
            <div>
              <p className="font-medium text-white">Thorpe Desktop</p>
              <p className="text-sm text-gray-400">
                Version {updateInfo?.current_version ?? "..."}
              </p>
            </div>
          </div>
          <button onClick={checkUpdates} disabled={checking} className="btn-secondary text-sm">
            <RefreshCw className={`h-4 w-4 ${checking ? "animate-spin" : ""}`} />
            Check for Updates
          </button>
        </div>

        {updateInfo && (
          <div className="rounded-lg border border-surface-border bg-surface p-4">
            {updateInfo.update_available ? (
              <div className="space-y-3">
                <p className="font-medium text-thorpe-400">
                  Update available: v{updateInfo.latest_version}
                </p>
                <p className="text-sm text-gray-300">{updateInfo.release_notes}</p>
                <button
                  type="button"
                  onClick={() => openUrl(updateInfo.download_url)}
                  className="btn-primary inline-flex text-sm"
                >
                  <Download className="h-4 w-4" /> Download Update
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-400" />
                <p className="text-sm text-gray-300">{updateInfo.release_notes}</p>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="card space-y-4">
        <div className="flex items-center justify-between gap-3">
          <h3 className="font-medium text-white">Download Installers</h3>
          <button
            type="button"
            onClick={() => openUrl(THORPE_DOWNLOADS.releasesPage)}
            className="inline-flex items-center gap-1 text-sm text-thorpe-400 hover:text-thorpe-300"
          >
            All releases <ExternalLink className="h-3.5 w-3.5" />
          </button>
        </div>
        <p className="text-sm text-gray-400">
          Use the latest public release. If a download says &ldquo;No permissions&rdquo;, make sure you
          are on the published release (not a draft) or use the direct links below.
        </p>
        <div className="grid gap-2">
          {PLATFORM_DOWNLOADS.map((item) => (
            <button
              key={item.label}
              type="button"
              onClick={() => openUrl(item.href)}
              className="flex items-center justify-between rounded-lg border border-surface-border bg-surface px-4 py-3 text-left text-sm text-gray-200 transition-colors hover:border-thorpe-500/40 hover:bg-thorpe-600/5"
            >
              <span>{item.label}</span>
              <Download className="h-4 w-4 text-thorpe-400" />
            </button>
          ))}
        </div>
      </div>

      <div className="card">
        <h3 className="mb-3 font-medium text-white">Supported Platforms</h3>
        <div className="grid gap-2 text-sm text-gray-400">
          <p>Windows 10/11 — .exe installer, .msi</p>
          <p>macOS (Apple Silicon) — .dmg</p>
          <p>Linux — .AppImage, .deb</p>
        </div>
      </div>
    </div>
  );
}
