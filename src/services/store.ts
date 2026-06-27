import { create } from "zustand";
import type { DiagnosticReport, LicenseInfo, SystemScanResult } from "../services/types";

export interface Notification {
  id: string;
  type: "info" | "success" | "warning" | "error";
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

interface AppStore {
  license: LicenseInfo | null;
  lastScan: SystemScanResult | null;
  recentReports: DiagnosticReport[];
  notifications: Notification[];
  sidebarCollapsed: boolean;
  searchQuery: string;

  setLicense: (license: LicenseInfo) => void;
  setLastScan: (scan: SystemScanResult | null) => void;
  setRecentReports: (reports: DiagnosticReport[]) => void;
  addNotification: (notification: Omit<Notification, "id" | "timestamp" | "read">) => void;
  markNotificationRead: (id: string) => void;
  clearNotifications: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setSearchQuery: (query: string) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  license: null,
  lastScan: null,
  recentReports: [],
  notifications: [],
  sidebarCollapsed: false,
  searchQuery: "",

  setLicense: (license) => set({ license }),
  setLastScan: (scan) => set({ lastScan: scan }),
  setRecentReports: (reports) => set({ recentReports: reports }),

  addNotification: (notification) =>
    set((state) => ({
      notifications: [
        {
          ...notification,
          id: `notif-${Date.now()}`,
          timestamp: new Date().toISOString(),
          read: false,
        },
        ...state.notifications,
      ].slice(0, 50),
    })),

  markNotificationRead: (id) =>
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n
      ),
    })),

  clearNotifications: () => set({ notifications: [] }),
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
  setSearchQuery: (query) => set({ searchQuery: query }),
}));
