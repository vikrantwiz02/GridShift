import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface Props {
  co2Actual: number;
  co2Counterfactual: number;
}

export default function CarbonSavingsBar({ co2Actual, co2Counterfactual }: Props) {
  const data = [
    { label: "Baseline (24/7)", value: co2Counterfactual, color: "#6b7280" },
    { label: "GridShift", value: co2Actual, color: "#10b981" },
  ];

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <h2 className="text-sm font-medium text-gray-300 mb-4">
        CO₂ avoided today — kg
      </h2>
      <ResponsiveContainer width="100%" height={140}>
        <BarChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
          <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#6b7280" }} />
          <YAxis tick={{ fontSize: 11, fill: "#6b7280" }} unit=" kg" width={52} />
          <Tooltip
            contentStyle={{ backgroundColor: "#111827", border: "1px solid #374151" }}
            labelStyle={{ color: "#d1d5db" }}
            formatter={(v: number) => [`${v.toFixed(2)} kg`, "CO₂"]}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((d) => (
              <Cell key={d.label} fill={d.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
