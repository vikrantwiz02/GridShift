import axios from "axios";
import type {
  Certificate,
  ChainVerifyResult,
  ForecastPoint,
  OptimizeResponse,
  WorkloadBlock,
} from "@/types";

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api",
  timeout: 30_000,
});

export const api = {
  energy: {
    forecast: (): Promise<ForecastPoint[]> =>
      http.get<ForecastPoint[]>("/energy/forecast").then((r) => r.data),

    actuals: (startDate: string, endDate: string): Promise<ForecastPoint[]> =>
      http
        .get<ForecastPoint[]>("/energy/actuals", {
          params: { start_date: startDate, end_date: endDate },
        })
        .then((r) => r.data),
  },

  schedule: {
    optimize: (date: string): Promise<OptimizeResponse> =>
      http
        .post<OptimizeResponse>("/schedule/optimize", { date })
        .then((r) => r.data),

    current: (date: string): Promise<WorkloadBlock[]> =>
      http
        .get<WorkloadBlock[]>("/schedule/current", { params: { target_date: date } })
        .then((r) => r.data),
  },

  certificates: {
    list: (limit = 50, offset = 0): Promise<Certificate[]> =>
      http
        .get<Certificate[]>("/certificates", { params: { limit, offset } })
        .then((r) => r.data),

    get: (seq: number): Promise<Certificate> =>
      http.get<Certificate>(`/certificates/${seq}`).then((r) => r.data),

    verify: (): Promise<ChainVerifyResult> =>
      http.get<ChainVerifyResult>("/certificates/verify").then((r) => r.data),
  },
};
