import { useState } from "react";
import { useEnergyForecast } from "@/hooks/useEnergyForecast";
import { useCurrentSchedule } from "@/hooks/useSchedule";
import EnergyFlowChart from "@/components/charts/EnergyFlowChart";
import CarbonSavingsBar from "@/components/charts/CarbonSavingsBar";
import KpiCard from "@/components/cards/KpiCard";
import OptimizeButton from "@/components/cards/OptimizeButton";
import type { OptimizeResponse } from "@/types";

function today() {
  return new Date().toISOString().split("T")[0];
}

function SolverLog({ result }: { result: OptimizeResponse }) {
  const savingsPct = (
    (result.savings_jpy / result.counterfactual_cost_jpy) * 100
  ).toFixed(1);
  const co2Avoided = (result.counterfactual_co2_kg - result.total_co2_kg).toFixed(1);
  const rigsActive = result.blocks.filter((b) => b.rigs_scheduled > 0.5).length;
  const solvedAt = new Date().toLocaleTimeString("ja-JP", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZone: "Asia/Tokyo",
    hour12: false,
  });

  return (
    <div className="bg-gray-950 border border-gray-800/60 rounded-lg px-4 py-3 font-mono text-[11px] space-y-1">
      <div className="flex items-center gap-2 mb-2">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
        <span className="text-gray-500">LP solved · HiGHS · {solvedAt} JST</span>
      </div>
      <div className="grid grid-cols-4 gap-x-6 gap-y-1 text-gray-500">
        <span>cost</span>
        <span className="text-gray-300">
          ¥{result.total_cost_jpy.toLocaleString("ja-JP", { maximumFractionDigits: 0 })}
        </span>
        <span>counterfactual</span>
        <span className="text-gray-400">
          ¥{result.counterfactual_cost_jpy.toLocaleString("ja-JP", { maximumFractionDigits: 0 })}
        </span>

        <span>savings</span>
        <span className="text-emerald-400">
          ¥{result.savings_jpy.toLocaleString("ja-JP", { maximumFractionDigits: 0 })} ({savingsPct}%)
        </span>
        <span>co₂ avoided</span>
        <span className="text-emerald-400">{co2Avoided} kg</span>

        <span>ren. fraction</span>
        <span className="text-blue-400">{(result.renewable_fraction * 100).toFixed(1)}%</span>
        <span>active hours</span>
        <span className="text-gray-300">{rigsActive} / 24 slots</span>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const date = today();
  const [lastResult, setLastResult] = useState<OptimizeResponse | null>(null);

  const { data: forecast = [], isLoading: forecastLoading } = useEnergyForecast();
  const { data: schedule = [] } = useCurrentSchedule(date);

  const savingsStr = lastResult
    ? `¥${lastResult.savings_jpy.toLocaleString("ja-JP", { maximumFractionDigits: 0 })}`
    : "—";
  const fractionStr = lastResult
    ? `${(lastResult.renewable_fraction * 100).toFixed(1)}%`
    : "—";
  const co2AvoidedKg = lastResult
    ? lastResult.counterfactual_co2_kg - lastResult.total_co2_kg
    : 0;
  const co2Str = lastResult ? `${co2AvoidedKg.toFixed(1)} kg` : "—";

  const savingsDelta = lastResult
    ? `${((lastResult.savings_jpy / lastResult.counterfactual_cost_jpy) * 100).toFixed(1)}% vs baseline`
    : undefined;

  return (
    <div className="space-y-4 max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-sm font-mono font-medium text-gray-300">{date}</h1>
          <p className="text-[10px] text-gray-600 mt-0.5">Yokohama · 35.44°N 139.63°E · 40 rigs · 3.25 kW each</p>
        </div>
        <OptimizeButton date={date} onSuccess={setLastResult} />
      </div>

      <div className="grid grid-cols-3 gap-3">
        <KpiCard
          label="Cost savings"
          value={savingsStr}
          sub="vs. continuous grid import"
          accent="green"
          delta={savingsDelta}
          isEmpty={!lastResult}
        />
        <KpiCard
          label="Renewable fraction"
          value={fractionStr}
          sub="of total kWh consumed"
          accent="blue"
          isEmpty={!lastResult}
        />
        <KpiCard
          label="CO₂ avoided"
          value={co2Str}
          sub="vs. 24/7 grid baseline"
          accent="amber"
          isEmpty={!lastResult}
        />
      </div>

      {lastResult && <SolverLog result={lastResult} />}

      {forecastLoading ? (
        <div className="h-64 bg-gray-900/60 rounded-lg border border-gray-800/60 animate-pulse" />
      ) : (
        <EnergyFlowChart forecast={forecast} schedule={schedule} />
      )}

      {lastResult && (
        <CarbonSavingsBar
          co2Actual={lastResult.total_co2_kg}
          co2Counterfactual={lastResult.counterfactual_co2_kg}
        />
      )}
    </div>
  );
}
