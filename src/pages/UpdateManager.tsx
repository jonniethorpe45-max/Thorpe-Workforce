import { useEffect, useState } from "react";
import { Download, CheckCircle, RefreshCw } from "lucide-react";
import { thorpeApi } from "../services/tauri";
import type { UpdateInfo } from "../services/types";

export function UpdateManager() {
  const [updateInfo, setUpdateInfo] = useState<UpdateInfo | null>(null);
  const [checking, setChecking] = useState(false);

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
                <a
                  href={updateInfo.download_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-primary inline-flex text-sm"
                >
                  <Download className="h-4 w-4" /> Download Update
                </a>
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

      <div className="card">
        <h3 className="mb-3 font-medium text-white">Supported Platforms</h3>
        <div className="grid gap-2 text-sm text-gray-400">
          <p>Windows 10/11 — .exe installer, .msi</p>
          <p>macOS (Intel & Apple Silicon) — .dmg</p>
          <p>Linux — .AppImage, .deb</p>
        </div>
      </div>
    </div>
  );
}
