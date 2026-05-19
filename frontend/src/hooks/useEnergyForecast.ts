import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";

export function useEnergyForecast() {
  return useQuery({
    queryKey: ["energy", "forecast"],
    queryFn: api.energy.forecast,
    refetchInterval: 5 * 60 * 1000,  // every 5 minutes
    staleTime: 4 * 60 * 1000,
  });
}
