export interface AgentMessage {
  id: string;
  role: 'agent' | 'user';
  content: string;
  timestamp: string;
  section: number;
}

export interface IntakeSchemaV10 {
  _schema_version: 'v10.0';
  // Note: Full schema definition will be added as we build each section
  [key: string]: any;
}
