import { Bell, Check, X } from "lucide-react";
import { useState } from "react";
import { useAppStore } from "../../services/store";
import { clsx } from "clsx";

export function NotificationCenter() {
  const [open, setOpen] = useState(false);
  const { notifications, markNotificationRead, clearNotifications } = useAppStore();
  const unreadCount = notifications.filter((n) => !n.read).length;

  const typeColors = {
    info: "text-thorpe-400",
    success: "text-green-400",
    warning: "text-yellow-400",
    error: "text-red-400",
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="relative rounded-lg p-2 text-gray-400 transition-colors hover:bg-surface-overlay hover:text-gray-200"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-thorpe-600 text-[10px] font-bold text-white">
            {unreadCount}
          </span>
        )}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-[100]" onClick={() => setOpen(false)} aria-hidden="true" />
          <div
            role="dialog"
            aria-label="Notifications"
            className="fixed right-6 top-16 z-[110] w-80 animate-slide-in rounded-xl border border-surface-border bg-surface-raised shadow-2xl"
          >
            <div className="flex items-center justify-between border-b border-surface-border px-4 py-3">
              <h3 className="font-semibold text-white">Notifications</h3>
              <div className="flex gap-1">
                {notifications.length > 0 && (
                  <button
                    onClick={clearNotifications}
                    className="rounded p-1 text-gray-400 hover:text-gray-200"
                    title="Clear all"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
            <div className="max-h-80 overflow-y-auto">
              {notifications.length === 0 ? (
                <p className="p-4 text-center text-sm text-gray-500">No notifications</p>
              ) : (
                notifications.map((n) => (
                  <div
                    key={n.id}
                    className={clsx(
                      "border-b border-surface-border/50 px-4 py-3 transition-colors",
                      !n.read && "bg-thorpe-600/5"
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className={clsx("text-sm font-medium", typeColors[n.type])}>{n.title}</p>
                        <p className="mt-0.5 text-xs text-gray-400">{n.message}</p>
                      </div>
                      {!n.read && (
                        <button
                          onClick={() => markNotificationRead(n.id)}
                          className="shrink-0 rounded p-1 text-gray-500 hover:text-gray-300"
                        >
                          <Check className="h-3 w-3" />
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
