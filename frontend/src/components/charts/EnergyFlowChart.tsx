import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ForecastPoint, WorkloadBlock } from "@/types";

interface Props {
  forecast: ForecastPoint[];
  schedule: WorkloadBlock[];
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-gray-950 border border-gray-700 rounded px-3 py-2 text-[11px] font-mono">
      <p className="text-gray-400 mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.color }}>
          {p.name}: {p.value.toFixed(1)} kW
        </p>
      ))}
    </div>
  );
}

export default function EnergyFlowChart({ forecast, schedule }: Props) {
  const currentHour = new Date().getHours();

  const data = forecast.map((f, i) => {
    const block = schedule.find((b) => b.slot_index === i);
    const hour = new Date(f.timestamp).getHours();
    return {
      hour: `${String(hour).padStart(2, "0")}:00`,
      solar: +f.solar_kw.toFixed(2),
      wind: +f.wind_kw.toFixed(2),
      load: block ? +block.load_kw.toFixed(2) : 0,
    };
  });

  const maxVal = Math.max(...data.map((d) => d.solar + d.wind + 10));

  return (
    <div className="bg-gray-900/60 rounded-lg p-4 border border-gray-800/60">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-[11px] font-mono text-gray-500 uppercase tracking-wider">
          Energy flow — next 24 h
        </h2>
        <div className="flex items-center gap-4 text-[10px] font-mono text-gray-600">
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-0.5 bg-amber-400 rounded" />
            solar
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-0.5 bg-blue-400 rounded" />
            wind
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-0.5 bg-orange-400 rounded" />
            rig load
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id="solarFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#fbbf24" stopOpacity={0.25} />
              <stop offset="100%" stopColor="#fbbf24" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="windFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#60a5fa" stopOpacity={0.2} />
              <stop offset="100%" stopColor="#60a5fa" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="2 4" stroke="#1f2937" vertical={false} />
          <XAxis
            dataKey="hour"
            tick={{ fontSize: 10, fill: "#4b5563", fontFamily: "monospace" }}
            axisLine={false}
            tickLine={false}
            interval={3}
          />
          <YAxis
            tick={{ fontSize: 10, fill: "#4b5563", fontFamily: "monospace" }}
            axisLine={false}
            tickLine={false}
            unit=" kW"
            width={54}
            domain={[0, maxVal]}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine
            x={`${String(currentHour).padStart(2, "0")}:00`}
            stroke="#374151"
            strokeDasharray="3 3"
            label={{ value: "now", fill: "#4b5563", fontSize: 9, fontFamily: "monospace" }}
          />
          <Area
            type="monotone"
            dataKey="solar"
            name="solar"
            stackId="ren"
            stroke="#fbbf24"
            fill="url(#solarFill)"
            strokeWidth={1.5}
          />
          <Area
            type="monotone"
            dataKey="wind"
            name="wind"
            stackId="ren"
            stroke="#60a5fa"
            fill="url(#windFill)"
            strokeWidth={1.5}
          />
          <Line
            type="stepAfter"
            dataKey="load"
            name="load"
            stroke="#f97316"
            strokeWidth={1.5}
            dot={false}
            strokeDasharray="none"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
