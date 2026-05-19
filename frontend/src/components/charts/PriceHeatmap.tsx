interface HeatmapRow {
  label: string;
  prices: (number | null)[];  // 24 hourly prices
}

interface Props {
  rows: HeatmapRow[];
}

function priceToColor(price: number | null, min: number, max: number): string {
  if (price === null) return "#1f2937";
  const t = Math.max(0, Math.min(1, (price - min) / (max - min || 1)));
  // Yellow (#fbbf24) → Red (#dc2626)
  const r = Math.round(251 + t * (220 - 251));
  const g = Math.round(191 + t * (38 - 191));
  const b = Math.round(36 + t * (38 - 36));
  return `rgb(${r},${g},${b})`;
}

export default function PriceHeatmap({ rows }: Props) {
  const allPrices = rows.flatMap((r) => r.prices).filter((p): p is number => p !== null);
  const min = Math.min(...allPrices);
  const max = Math.max(...allPrices);

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <h2 className="text-sm font-medium text-gray-300 mb-3">
        Grid price heatmap — JPY/kWh
      </h2>

      <div className="overflow-x-auto">
        <table className="border-collapse text-xs">
          <thead>
            <tr>
              <th className="w-16 text-gray-600 font-normal pr-2 text-right text-[10px]" />
              {Array.from({ length: 24 }, (_, h) => (
                <th
                  key={h}
                  className="w-6 text-center text-gray-600 font-normal pb-1 text-[10px]"
                >
                  {h % 6 === 0 ? h : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label}>
                <td className="text-gray-500 text-right pr-2 text-[10px] whitespace-nowrap">
                  {row.label}
                </td>
                {row.prices.map((price, h) => (
                  <td key={h} className="p-px">
                    <div
                      className="w-5 h-5 rounded-sm"
                      style={{ backgroundColor: priceToColor(price, min, max) }}
                      title={price !== null ? `${h}:00 — ¥${price.toFixed(2)}/kWh` : "no data"}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>

        <div className="flex items-center gap-2 mt-3">
          <span className="text-[10px] text-gray-600">¥{min.toFixed(0)}</span>
          <div
            className="h-2 w-32 rounded"
            style={{
              background: "linear-gradient(to right, #fbbf24, #dc2626)",
            }}
          />
          <span className="text-[10px] text-gray-600">¥{max.toFixed(0)}</span>
        </div>
      </div>
    </div>
  );
}
