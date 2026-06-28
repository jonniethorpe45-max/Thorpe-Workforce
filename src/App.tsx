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
import { FeatureRoute } from "./components/auth/FeatureRoute";

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
          <Route
            path="/enterprise/ai"
            element={
              <FeatureRoute
                feature="enterprise_ai_console"
                title="Enterprise AI Console"
                description="Requires an Enterprise license. Manage multi-provider AI keys, budgets, and org policy."
              >
                <EnterpriseAiConsole />
              </FeatureRoute>
            }
          />
          <Route
            path="/intelligence"
            element={
              <FeatureRoute
                feature="intelligence_console"
                title="Intelligence Console"
                description="Requires an Enterprise license. Access threat intel, org playbooks, repair packs, and agent sessions."
              >
                <IntelligenceConsole />
              </FeatureRoute>
            }
          />
          <Route path="/updates" element={<UpdateManager />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
