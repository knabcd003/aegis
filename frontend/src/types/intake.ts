export interface AgentMessage {
  id: string;
  role: 'agent' | 'user';
  content: string;
  timestamp: string;
  section: number;
}

export interface FundamentalScreen {
  id: string;
  screen_type: string | null;
  threshold: number | null;
  flexibility: string | null;
  applies_to_catalyst_types: string[];
  custom_description: string | null;
}

export interface RiskAcknowledgment {
  key: string;
  label: string;
  description: string;
  required_for: string[];
}

export interface CatalystTypeEntry {
  catalyst_type: string;
  permitted: boolean;
  risk_acknowledgments: {
    iv_crush_risk_acknowledged: boolean;
    gap_risk_acknowledged: boolean;
    binary_event_risk_acknowledged: boolean;
    information_leakage_risk_acknowledged: boolean;
    pre_revenue_universe_acknowledged: boolean;
  };
}

export interface IntakeSchemaV10 {
  _schema_version: 'v10.0';
  // Note: Full schema definition will be added as we build each section
  [key: string]: any;
}
