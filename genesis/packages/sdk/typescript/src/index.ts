export type IntentRequest = {
  message: string;
  user_id?: string;
};

export type IntentResult = {
  intent: {
    type: string;
    capability: string | null;
    summary: string;
    entities: Record<string, unknown>;
  };
  plan: {
    steps: Array<{ id: string; description: string }>;
    capability: string | null;
  };
  policy: {
    decision: "allow" | "block";
    risk_level: string;
    requires_approval: boolean;
    reason: string;
    capability_result?: Record<string, unknown>;
  };
  execution: {
    status: string;
    approval_id: string | null;
  };
  explanation: string;
};

export type Approval = {
  id: string;
  user_id: string;
  intent: IntentResult["intent"];
  plan: IntentResult["plan"];
  policy: IntentResult["policy"];
  status: string;
  created_at: string;
  updated_at: string;
};

export type AuditEvent = {
  id: string;
  event_type: string;
  user_id: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export type ServiceInfo = {
  id: string;
  name: string;
  port: number;
  status: string;
};

export type Capability = {
  id: string;
  name: string;
  description?: string;
  risk_level: string;
  connector: string;
  status: string;
};

export type ExecuteResult = {
  approval_id: string;
  executed_by: string;
  intent: IntentResult["intent"];
  policy: IntentResult["policy"];
  execution: {
    status: string;
    connector: string | null;
    result: Record<string, unknown> | null;
  };
  explanation: string;
};

export type GenesisClientOptions = {
  gatewayUrl?: string;
  userId?: string;
  fetchImpl?: typeof fetch;
};

async function request<T>(
  fetchImpl: typeof fetch,
  url: string,
  init?: RequestInit
): Promise<T> {
  const response = await fetchImpl(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Genesis API ${response.status}: ${text}`);
  }
  return (await response.json()) as T;
}

export class GenesisClient {
  readonly gatewayUrl: string;
  readonly userId: string;
  private readonly fetchImpl: typeof fetch;

  constructor(options: GenesisClientOptions = {}) {
    this.gatewayUrl = (options.gatewayUrl || "http://localhost:7999").replace(/\/$/, "");
    this.userId = options.userId || "demo-user";
    this.fetchImpl = options.fetchImpl || fetch.bind(globalThis);
  }

  intent(message: string, userId?: string): Promise<IntentResult> {
    return request<IntentResult>(this.fetchImpl, `${this.gatewayUrl}/gateway/intent`, {
      method: "POST",
      body: JSON.stringify({
        message,
        user_id: userId || this.userId,
      }),
    });
  }

  approve(approvalId: string, approvedBy?: string): Promise<Record<string, unknown>> {
    return request(this.fetchImpl, `${this.gatewayUrl}/gateway/approvals/approve`, {
      method: "POST",
      body: JSON.stringify({
        approval_id: approvalId,
        approved_by: approvedBy || this.userId,
      }),
    });
  }

  execute(approvalId: string, executedBy?: string): Promise<ExecuteResult> {
    return request<ExecuteResult>(this.fetchImpl, `${this.gatewayUrl}/gateway/execute`, {
      method: "POST",
      body: JSON.stringify({
        approval_id: approvalId,
        executed_by: executedBy || this.userId,
      }),
    });
  }

  audit(): Promise<AuditEvent[]> {
    return request(this.fetchImpl, `${this.gatewayUrl}/gateway/audit`);
  }

  approvals(): Promise<Approval[]> {
    return request(this.fetchImpl, `${this.gatewayUrl}/gateway/approvals`);
  }

  services(): Promise<ServiceInfo[]> {
    return request(this.fetchImpl, `${this.gatewayUrl}/gateway/services`);
  }

  capabilities(): Promise<Capability[]> {
    return request(this.fetchImpl, `${this.gatewayUrl}/gateway/capabilities`);
  }
}

export function createGenesisClient(options?: GenesisClientOptions): GenesisClient {
  return new GenesisClient(options);
}
