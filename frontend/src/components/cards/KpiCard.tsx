interface Props {
  label: string;
  value: string;
  sub?: string;
  accent?: "green" | "blue" | "amber";
  delta?: string;
  isEmpty?: boolean;
}

const styles = {
  green: {
    border: "border-l-emerald-500",
    value: "text-emerald-400",
    glow: "shadow-[inset_0_1px_0_0_rgba(52,211,153,0.07)]",
    delta: "text-emerald-500",
  },
  blue: {
    border: "border-l-blue-500",
    value: "text-blue-400",
    glow: "shadow-[inset_0_1px_0_0_rgba(96,165,250,0.07)]",
    delta: "text-blue-500",
  },
  amber: {
    border: "border-l-amber-500",
    value: "text-amber-400",
    glow: "shadow-[inset_0_1px_0_0_rgba(251,191,36,0.07)]",
    delta: "text-amber-500",
  },
};

export default function KpiCard({ label, value, sub, accent = "green", delta, isEmpty }: Props) {
  const s = styles[accent];
  return (
    <div
      className={`bg-gray-900/60 rounded-lg p-4 border border-gray-800/80 border-l-2 ${s.border} ${s.glow} flex flex-col gap-1`}
    >
      <p className="text-[10px] text-gray-600 uppercase tracking-widest font-mono">{label}</p>
      <p
        className={`text-xl font-mono font-semibold tabular-nums mt-0.5 ${
          isEmpty ? "text-gray-700" : s.value
        }`}
      >
        {value}
      </p>
      <div className="flex items-center justify-between mt-0.5">
        {sub && <p className="text-[10px] text-gray-600">{sub}</p>}
        {delta && !isEmpty && (
          <span className={`text-[10px] font-mono ${s.delta}`}>{delta}</span>
        )}
      </div>
    </div>
  );
}
