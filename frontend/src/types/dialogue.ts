/** Mirrors backend/schemas/dialogue.py and nested service payloads. */

export interface EntityPrediction {
  entity_type: string;
  value: string;
  start: number;
  end: number;
  confidence: number;
}

export interface NLUPayload {
  text: string;
  intent: string;
  intent_confidence: number;
  entities: EntityPrediction[];
}

export interface DialoguePayload {
  reply: string;
  state: string;
  slots: Record<string, string>;
  intent: string;
  ready_for_external_query: boolean;
  blocked_reason: string | null;
}

export interface CVERecord {
  cve_id: string;
  description: string;
  cvss_score: number | null;
  severity: string | null;
  products: string[];
  versions: string[];
}

export interface MitreTechnique {
  technique_id: string;
  name: string;
  tactic: string;
}

export interface RetrievalPayload {
  intent?: string;
  source?: string;
  cves?: CVERecord[];
  mitre_techniques?: MitreTechnique[];
  errors?: string[];
  raw_count?: number;
}

export interface DialogueMessageRequest {
  text: string;
  session_id?: string | null;
}

export interface DialogueMessageResponse {
  session_id: string;
  reply: string;
  dialogue: DialoguePayload;
  nlu: NLUPayload;
  retrieval: RetrievalPayload | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  meta?: DialogueMessageResponse;
}
