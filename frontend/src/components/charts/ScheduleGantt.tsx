import { useState } from "react";
import type { WorkloadBlock } from "@/types";

interface TooltipState {
  x: number;
  y: number;
  block: WorkloadBlock;
}

interface Props {
  blocks: WorkloadBlock[];
  numRigs?: number;
}

const W = 680;
const ROW_H = 18;
const ROW_GAP = 2;
const LABEL_W = 40;
const HOURS = 24;

export default function ScheduleGantt({ blocks, numRigs = 40 }: Props) {
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);

  const innerW = W - LABEL_W;
  const slotW = innerW / HOURS;
  const totalH = numRigs * (ROW_H + ROW_GAP);
  const slotMap = new Map(blocks.map((b) => [b.slot_index, b]));
  const currentHour = new Date().getHours();

  return (
    <div className="bg-gray-900/60 rounded-lg p-4 border border-gray-800/60">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-[11px] font-mono text-gray-500 uppercase tracking-wider">
          Dispatch schedule — 24 h
        </h2>
        <div className="flex items-center gap-4 text-[10px] font-mono text-gray-600">
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-2 rounded-sm bg-emerald-500/70" />
            renewable
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-2 rounded-sm bg-gray-600" />
            grid import
          </span>
        </div>
      </div>

      <div className="relative overflow-x-auto" onMouseLeave={() => setTooltip(null)}>
        <svg width={W} height={totalH + 20} className="block">
          {/* Hour ticks */}
          {Array.from({ length: HOURS + 1 }, (_, h) => (
            <g key={h}>
              <line
                x1={LABEL_W + h * slotW}
                y1={0}
                x2={LABEL_W + h * slotW}
                y2={totalH}
                stroke="#1f2937"
                strokeWidth={1}
              />
              {h % 6 === 0 && (
                <text
                  x={LABEL_W + h * slotW}
                  y={totalH + 14}
                  fontSize={9}
                  fill="#4b5563"
                  textAnchor="middle"
                  fontFamily="monospace"
                >
                  {h < HOURS ? `${String(h).padStart(2, "0")}:00` : ""}
                </text>
              )}
            </g>
          ))}

          {/* "now" marker */}
          <line
            x1={LABEL_W + currentHour * slotW}
            y1={0}
            x2={LABEL_W + currentHour * slotW}
            y2={totalH}
            stroke="#374151"
            strokeWidth={1}
            strokeDasharray="3 3"
          />

          {/* Rig rows */}
          {Array.from({ length: numRigs }, (_, rig) => {
            const y = rig * (ROW_H + ROW_GAP);
            return (
              <g key={rig}>
                {rig % 10 === 0 && (
                  <text
                    x={LABEL_W - 5}
                    y={y + ROW_H - 5}
                    fontSize={8}
                    fill="#374151"
                    textAnchor="end"
                    fontFamily="monospace"
                  >
                    R{rig + 1}
                  </text>
                )}

                {Array.from({ length: HOURS }, (_, hour) => {
                  const block = slotMap.get(hour);
                  if (!block) return null;
                  const rigsOn = Math.round(block.rigs_scheduled);
                  if (rig >= rigsOn) return null;

                  const onRenewable = block.grid_import_kw < 0.5;
                  return (
                    <rect
                      key={hour}
                      x={LABEL_W + hour * slotW + 0.5}
                      y={y + 1}
                      width={slotW - 1}
                      height={ROW_H - 2}
                      rx={1}
                      fill={onRenewable ? "#10b981" : "#4b5563"}
                      opacity={0.8}
                      style={{ cursor: "default" }}
                      onMouseEnter={(e) =>
                        setTooltip({ x: e.clientX, y: e.clientY, block })
                      }
                    />
                  );
                })}
              </g>
            );
          })}
        </svg>

        {tooltip && (
          <div
            className="fixed z-50 bg-gray-950 border border-gray-700 rounded px-3 py-2 text-[10px] font-mono pointer-events-none shadow-xl"
            style={{ left: tooltip.x + 14, top: tooltip.y - 50 }}
          >
            <p className="text-gray-400 mb-1">
              {String(tooltip.block.slot_index).padStart(2, "0")}:00 — {String(tooltip.block.slot_index + 1).padStart(2, "0")}:00
            </p>
            <p className="text-gray-300">rigs: {tooltip.block.rigs_scheduled.toFixed(1)}</p>
            <p className="text-gray-300">load: {tooltip.block.load_kw.toFixed(1)} kW</p>
            <p className="text-emerald-400">ren avail: {tooltip.block.renewable_kw_available.toFixed(1)} kW</p>
            <p className="text-gray-400">grid import: {tooltip.block.grid_import_kw.toFixed(1)} kW</p>
            <p className="text-amber-400">price: ¥{tooltip.block.price_jpy_kwh.toFixed(2)}/kWh</p>
          </div>
        )}
      </div>
    </div>
  );
}
