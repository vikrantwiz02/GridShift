export interface ForecastPoint {
  timestamp: string;
  solar_kw: number;
  wind_kw: number;
  total_renewable_kw: number;
  price_jpy_kwh: number;
  carbon_g_kwh: number;
}

export interface WorkloadBlock {
  id: number;
  created_at: string;
  date: string;
  slot_index: number;
  rigs_scheduled: number;
  load_kw: number;
  renewable_kw_available: number;
  price_jpy_kwh: number;
  grid_import_kw: number;
  status: string;
}

export interface OptimizeResponse {
  date: string;
  total_cost_jpy: number;
  counterfactual_cost_jpy: number;
  savings_jpy: number;
  renewable_fraction: number;
  total_co2_kg: number;
  counterfactual_co2_kg: number;
  blocks: WorkloadBlock[];
}

export interface Certificate {
  seq: number;
  issued_at: string;
  prev_hash: string;
  payload_hash: string;
  cert_hash: string;
  data_json: string;
}

export interface ChainVerifyResult {
  valid: boolean;
  total_certs: number;
  broken_at_seq: number | null;
  message: string;
}
