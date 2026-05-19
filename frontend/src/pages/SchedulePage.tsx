import { useState } from "react";
import { useCurrentSchedule } from "@/hooks/useSchedule";
import ScheduleGantt from "@/components/charts/ScheduleGantt";
import PriceHeatmap from "@/components/charts/PriceHeatmap";
import type { WorkloadBlock } from "@/types";

// Static 7-day price profile (JEPX 2024 Kanto averages) for the heatmap.
// In production this would come from the DB via GET /energy/actuals.
const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const DIURNAL = [8.2, 7.8, 7.4, 7.1, 7.3, 8.5, 11.2, 14.7, 16.3, 15.8, 14.1,
  13.2, 12.9, 13.1, 13.8, 14.5, 16.0, 18.7, 19.4, 17.3, 15.1, 13.2, 11.0, 9.3];

const heatmapRows = DAYS.map((label, d) => ({
  label,
  prices: DIURNAL.map((p) => p * (0.9 + Math.sin(d * 0.7 + 1.2) * 0.1)),
}));

function today() {
  return new Date().toISOString().split("T")[0];
}

export default function SchedulePage() {
  const date = today();
  const { data: schedule = [], isLoading } = useCurrentSchedule(date);

  return (
    <div className="space-y-6 max-w-5xl">
      <h1 className="text-base font-semibold text-gray-200">Schedule — {date}</h1>

      {isLoading ? (
        <div className="h-64 bg-gray-900 rounded-xl border border-gray-800 animate-pulse" />
      ) : schedule.length === 0 ? (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-8 text-sm text-gray-600 text-center">
          No schedule found for today. Go to the Dashboard and run the optimizer.
        </div>
      ) : (
        <ScheduleGantt blocks={schedule} numRigs={40} />
      )}

      <PriceHeatmap rows={heatmapRows} />
    </div>
  );
}
