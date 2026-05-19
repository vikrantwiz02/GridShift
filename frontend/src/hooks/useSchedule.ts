import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";

export function useCurrentSchedule(date: string) {
  return useQuery({
    queryKey: ["schedule", "current", date],
    queryFn: () => api.schedule.current(date),
  });
}

export function useOptimize() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (date: string) => api.schedule.optimize(date),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["schedule", "current", data.date] });
      queryClient.invalidateQueries({ queryKey: ["certificates"] });
    },
  });
}
