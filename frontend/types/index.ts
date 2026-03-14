export type Worker = {
  id: string;
  name: string;
  goal: string;
  status: string;
  tone: string;
  send_limit_per_day: number;
};

export type Campaign = {
  id: string;
  name: string;
  status: string;
  target_industry?: string;
  target_roles?: string[];
  target_locations?: string[];
};

export type Lead = {
  id: string;
  company_name: string;
  full_name?: string;
  title?: string;
  email: string;
  lead_status: string;
  location?: string;
};

export type Reply = {
  id: string;
  reply_text: string;
  intent_classification: string;
  requires_human_review: boolean;
  created_at: string;
};

export type Meeting = {
  id: string;
  lead_id: string;
  calendar_provider: string;
  scheduled_start: string;
  scheduled_end: string;
  meeting_status: string;
};
