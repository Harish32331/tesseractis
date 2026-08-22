export type UserRole = "user" | "admin";
export type UserStatus = "active" | "disabled";

export interface UserPublic {
  id: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  created_at: string;
}

export type ConfidenceBand = "high" | "medium" | "low" | "unknown";
export type ScanStatus = "pending" | "processing" | "completed" | "failed";

export interface ScanObjectPublic {
  category_code: string;
  confidence: number;
  evidence: string[];
}

export interface ScanPublic {
  id: string;
  status: ScanStatus;
  overall_confidence: number | null;
  confidence_band: ConfidenceBand | null;
  needs_review: boolean;
  explanation: string | null;
  limitations: string[];
  is_mock_result: boolean;
  model_provider: string | null;
  model_version: string | null;
  objects: ScanObjectPublic[];
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface ScanSummary {
  id: string;
  status: ScanStatus;
  overall_confidence: number | null;
  confidence_band: ConfidenceBand | null;
  needs_review: boolean;
  created_at: string;
}

export interface AdminAnalytics {
  data_source: string;
  total_users: number;
  total_scans: number;
  completed_scans: number;
  needs_review_scans: number;
  failed_scans: number;
  note: string;
}
