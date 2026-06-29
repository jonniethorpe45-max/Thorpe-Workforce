import { useEffect, useState } from "react";
import { Briefcase, Plus, Users, FileText, StickyNote } from "lucide-react";
import { Link } from "react-router-dom";
import { thorpeApi } from "../services/tauri";
import { useAppStore } from "../services/store";
import type { Client, SupportCase, TechnicianNote } from "../services/types";

export function TechnicianWorkspace() {
  const [featureAllowed, setFeatureAllowed] = useState<boolean | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [cases, setCases] = useState<SupportCase[]>([]);
  const [notes, setNotes] = useState<TechnicianNote[]>([]);
  const [activeTab, setActiveTab] = useState<"cases" | "clients" | "notes">("cases");
  const [showNewClient, setShowNewClient] = useState(false);
  const [showNewCase, setShowNewCase] = useState(false);
  const { addNotification } = useAppStore();

  useEffect(() => {
    thorpeApi.checkFeature("technician_workspace").then((f) => {
      setFeatureAllowed(f.allowed);
      if (f.allowed) loadData();
    });
  }, []);

  const loadData = async () => {
    const [c, cs, n] = await Promise.all([
      thorpeApi.listClients(),
      thorpeApi.listCases(),
      thorpeApi.listTechnicianNotes(),
    ]);
    setClients(c);
    setCases(cs);
    setNotes(n);
  };

  if (featureAllowed === false) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20 animate-fade-in">
        <Briefcase className="h-16 w-16 text-gray-600" />
        <h2 className="text-xl font-bold text-white">Technician Workspace</h2>
        <p className="max-w-md text-center text-gray-400">
          The Technician Workspace requires an Enterprise license for case management, client
          records, and team collaboration.
        </p>
        <Link to="/licensing" className="btn-primary">
          View Licensing
        </Link>
      </div>
    );
  }

  if (featureAllowed === null) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-thorpe-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Technician Workspace</h1>
          <p className="mt-1 text-gray-400">Manage support cases, clients, and technician notes.</p>
        </div>
      </div>

      <div className="flex gap-2 border-b border-surface-border">
        {[
          { id: "cases" as const, label: "Cases", icon: FileText },
          { id: "clients" as const, label: "Clients", icon: Users },
          { id: "notes" as const, label: "Notes", icon: StickyNote },
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              activeTab === id
                ? "border-thorpe-500 text-thorpe-400"
                : "border-transparent text-gray-400 hover:text-gray-200"
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {activeTab === "cases" && (
        <div>
          <div className="mb-4 flex justify-end">
            <button onClick={() => setShowNewCase(true)} className="btn-primary text-sm">
              <Plus className="h-4 w-4" /> New Case
            </button>
          </div>
          {showNewCase && (
            <NewCaseForm
              clients={clients}
              onClose={() => setShowNewCase(false)}
              onCreated={(c) => {
                setCases((prev) => [c, ...prev]);
                setShowNewCase(false);
                addNotification({ type: "success", title: "Case Created", message: c.title });
              }}
            />
          )}
          <div className="space-y-3">
            {cases.length === 0 ? (
              <div className="card py-8 text-center text-gray-400">No cases yet.</div>
            ) : (
              cases.map((c) => (
                <div key={c.id} className="card">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium text-white">{c.title}</h3>
                    <div className="flex gap-2">
                      <StatusBadge status={c.status} />
                      <PriorityBadge priority={c.priority} />
                    </div>
                  </div>
                  {c.description && <p className="mt-2 text-sm text-gray-400">{c.description}</p>}
                  <p className="mt-2 text-xs text-gray-500">
                    Updated {new Date(c.updated_at).toLocaleString()}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {activeTab === "clients" && (
        <div>
          <div className="mb-4 flex justify-end">
            <button onClick={() => setShowNewClient(true)} className="btn-primary text-sm">
              <Plus className="h-4 w-4" /> New Client
            </button>
          </div>
          {showNewClient && (
            <NewClientForm
              onClose={() => setShowNewClient(false)}
              onCreated={(c) => {
                setClients((prev) => [...prev, c]);
                setShowNewClient(false);
                addNotification({ type: "success", title: "Client Added", message: c.name });
              }}
            />
          )}
          <div className="grid gap-3 sm:grid-cols-2">
            {clients.length === 0 ? (
              <div className="card col-span-2 py-8 text-center text-gray-400">No clients yet.</div>
            ) : (
              clients.map((c) => (
                <div key={c.id} className="card">
                  <h3 className="font-medium text-white">{c.name}</h3>
                  {c.company && <p className="text-sm text-gray-400">{c.company}</p>}
                  {c.email && <p className="text-xs text-gray-500">{c.email}</p>}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {activeTab === "notes" && (
        <div className="space-y-3">
          {notes.length === 0 ? (
            <div className="card py-8 text-center text-gray-400">No technician notes yet.</div>
          ) : (
            notes.map((n) => (
              <div key={n.id} className="card">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-thorpe-400">{n.author}</span>
                  <span className="text-xs text-gray-500">
                    {new Date(n.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="mt-2 text-sm text-gray-300">{n.content}</p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    open: "bg-blue-500/15 text-blue-400",
    in_progress: "bg-yellow-500/15 text-yellow-400",
    closed: "bg-green-500/15 text-green-400",
  };
  return (
    <span className={`badge ${colors[status] || "bg-gray-500/15 text-gray-400"}`}>{status}</span>
  );
}

function PriorityBadge({ priority }: { priority: string }) {
  const colors: Record<string, string> = {
    low: "bg-gray-500/15 text-gray-400",
    medium: "bg-yellow-500/15 text-yellow-400",
    high: "bg-orange-500/15 text-orange-400",
    critical: "bg-red-500/15 text-red-400",
  };
  return (
    <span className={`badge ${colors[priority] || ""}`}>{priority}</span>
  );
}

function NewClientForm({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: (client: Client) => void;
}) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [company, setCompany] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const client = await thorpeApi.createClient({
      name,
      email: email || null,
      phone: null,
      company: company || null,
      notes: null,
    });
    onCreated(client);
  };

  return (
    <form onSubmit={handleSubmit} className="card mb-4 space-y-3">
      <h3 className="font-medium text-white">New Client</h3>
      <input className="input" placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} required />
      <input className="input" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <input className="input" placeholder="Company" value={company} onChange={(e) => setCompany(e.target.value)} />
      <div className="flex gap-2">
        <button type="submit" className="btn-primary text-sm">Create</button>
        <button type="button" onClick={onClose} className="btn-secondary text-sm">Cancel</button>
      </div>
    </form>
  );
}

function NewCaseForm({
  clients,
  onClose,
  onCreated,
}: {
  clients: Client[];
  onClose: () => void;
  onCreated: (c: SupportCase) => void;
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [clientId, setClientId] = useState("");
  const [priority, setPriority] = useState("medium");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const supportCase = await thorpeApi.createCase({
      title,
      description,
      client_id: clientId || undefined,
      status: "open",
      priority,
    });
    onCreated(supportCase);
  };

  return (
    <form onSubmit={handleSubmit} className="card mb-4 space-y-3">
      <h3 className="font-medium text-white">New Case</h3>
      <input className="input" placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} required />
      <textarea className="input" placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} rows={3} />
      <select className="input" value={clientId} onChange={(e) => setClientId(e.target.value)}>
        <option value="">No client</option>
        {clients.map((c) => (
          <option key={c.id} value={c.id}>{c.name}</option>
        ))}
      </select>
      <select className="input" value={priority} onChange={(e) => setPriority(e.target.value)}>
        <option value="low">Low</option>
        <option value="medium">Medium</option>
        <option value="high">High</option>
        <option value="critical">Critical</option>
      </select>
      <div className="flex gap-2">
        <button type="submit" className="btn-primary text-sm">Create</button>
        <button type="button" onClick={onClose} className="btn-secondary text-sm">Cancel</button>
      </div>
    </form>
  );
}
