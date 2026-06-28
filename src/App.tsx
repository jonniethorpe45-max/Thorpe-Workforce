import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { Dashboard } from "./pages/Dashboard";
import { JonathanAssistant } from "./pages/JonathanAssistant";
import { SystemScanner } from "./pages/SystemScanner";
import { DiagnosticReports } from "./pages/DiagnosticReports";
import { RepairCenter } from "./pages/RepairCenter";
import { TechnicianWorkspace } from "./pages/TechnicianWorkspace";
import { KnowledgeBase } from "./pages/KnowledgeBase";
import { SettingsPage } from "./pages/SettingsPage";
import { LicensingPage } from "./pages/LicensingPage";
import { UpdateManager } from "./pages/UpdateManager";
import { EnterpriseAiConsole } from "./pages/EnterpriseAiConsole";
import { IntelligenceConsole } from "./pages/IntelligenceConsole";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/jonathan" element={<JonathanAssistant />} />
          <Route path="/scanner" element={<SystemScanner />} />
          <Route path="/reports" element={<DiagnosticReports />} />
          <Route path="/repairs" element={<RepairCenter />} />
          <Route path="/workspace" element={<TechnicianWorkspace />} />
          <Route path="/knowledge" element={<KnowledgeBase />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/licensing" element={<LicensingPage />} />
          <Route path="/enterprise/ai" element={<EnterpriseAiConsole />} />
          <Route path="/intelligence" element={<IntelligenceConsole />} />
          <Route path="/updates" element={<UpdateManager />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
