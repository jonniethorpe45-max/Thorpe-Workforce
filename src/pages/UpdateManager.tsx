import { useEffect, useState } from "react";
import { Download, CheckCircle, RefreshCw, ExternalLink } from "lucide-react";
import { THORPE_RELEASES_PAGE } from "../config/downloads";
import { thorpeApi } from "../services/tauri";
import type { ReleaseDownloads, UpdateInfo } from "../services/types";

type PlatformDownload = { label: string; href: string };

function buildPlatformDownloads(downloads: ReleaseDownloads | null): PlatformDownload[] {
  if (!downloads) return [];

  const entries: Array<[string, string | null]> = [
    ["Windows (.exe)", downloads.windows_exe],
    ["Windows (.msi)", downloads.windows_msi],
    ["macOS Apple Silicon (.dmg)", downloads.macos_dmg],
    ["Linux (.AppImage)", downloads.linux_appimage],
    ["Linux (.deb)", downloads.linux_deb],
  ];

  return entries
    .filter((entry): entry is [string, string] => Boolean(entry[1]))
    .map(([label, href]) => ({ label, href }));
}

export function UpdateManager() {
  const [updateInfo, setUpdateInfo] = useState<UpdateInfo | null>(null);
  const [downloads, setDownloads] = useState<ReleaseDownloads | null>(null);
  const [checking, setChecking] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const openUrl = (url: string) => {
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const loadDownloads = async () => {
    try {
      const links = await thorpeApi.getReleaseDownloads();
      setDownloads(links);
      setDownloadError(null);
    } catch (err) {
      console.error(err);
      setDownloadError("Could not load installer links. Use the releases page below.");
    }
  };

  const checkUpdates = async () => {
    setChecking(true);
    try {
      const [info] = await Promise.all([thorpeApi.checkForUpdates(), loadDownloads()]);
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

  const platformDownloads = buildPlatformDownloads(downloads);

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
                {downloads?.release_version ? ` · Latest release v${downloads.release_version}` : ""}
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
            {updateInfo.check_error ? (
              <div className="space-y-2">
                <p className="font-medium text-warning">Update check failed</p>
                <p className="text-sm text-gray-300">{updateInfo.release_notes}</p>
                <p className="text-xs text-gray-500">{updateInfo.check_error}</p>
              </div>
            ) : updateInfo.update_available ? (
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
            onClick={() => openUrl(downloads?.releases_page ?? THORPE_RELEASES_PAGE)}
            className="inline-flex items-center gap-1 text-sm text-thorpe-400 hover:text-thorpe-300"
          >
            All releases <ExternalLink className="h-3.5 w-3.5" />
          </button>
        </div>
        <p className="text-sm text-gray-400">
          Links are loaded from the published GitHub release
          {downloads?.release_version ? ` (v${downloads.release_version})` : ""}. If a download says
          &ldquo;No permissions&rdquo;, the filename may not match the latest release — refresh this page or use
          the releases page.
        </p>
        {downloadError && <p className="text-sm text-warning">{downloadError}</p>}
        <div className="grid gap-2">
          {platformDownloads.length > 0 ? (
            platformDownloads.map((item) => (
              <button
                key={item.label}
                type="button"
                onClick={() => openUrl(item.href)}
                className="flex items-center justify-between rounded-lg border border-surface-border bg-surface px-4 py-3 text-left text-sm text-gray-200 transition-colors hover:border-thorpe-500/40 hover:bg-thorpe-600/5"
              >
                <span>{item.label}</span>
                <Download className="h-4 w-4 text-thorpe-400" />
              </button>
            ))
          ) : (
            <button
              type="button"
              onClick={() => openUrl(THORPE_RELEASES_PAGE)}
              className="btn-secondary text-sm"
            >
              Open GitHub Releases
            </button>
          )}
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
