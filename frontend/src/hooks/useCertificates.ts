import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";

export function useCertificates(limit = 50) {
  return useQuery({
    queryKey: ["certificates", limit],
    queryFn: () => api.certificates.list(limit),
  });
}

export function useCertificate(seq: number | null) {
  return useQuery({
    queryKey: ["certificate", seq],
    queryFn: () => api.certificates.get(seq!),
    enabled: seq !== null,
  });
}

export function useChainVerify() {
  return useQuery({
    queryKey: ["certificates", "verify"],
    queryFn: api.certificates.verify,
    staleTime: 30_000,
  });
}
