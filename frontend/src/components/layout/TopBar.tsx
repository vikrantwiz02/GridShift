import { useEffect, useState } from "react";
import { useEnergyForecast } from "@/hooks/useEnergyForecast";

function LiveClock() {
  const [time, setTime] = useState(() =>
    new Date().toLocaleTimeString("ja-JP", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      timeZone: "Asia/Tokyo",
      hour12: false,
    })
  );

  useEffect(() => {
    const id = setInterval(() => {
      setTime(
        new Date().toLocaleTimeString("ja-JP", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          timeZone: "Asia/Tokyo",
          hour12: false,
        })
      );
    }, 1000);
    return () => clearInterval(id);
  }, []);

  return <span className="font-mono text-gray-400 tabular-nums">{time} JST</span>;
}

export default function TopBar() {
  const { data: forecast, isLoading, isError } = useEnergyForecast();

  const currentHour = new Date().getHours();
  const currentSlot = forecast?.[currentHour];
  const totalRenewable = currentSlot
    ? (currentSlot.solar_kw + currentSlot.wind_kw).toFixed(1)
    : null;

  return (
    <header className="h-10 bg-gray-950 border-b border-gray-800/60 flex items-center justify-between px-5 shrink-0">
      <div className="flex items-center gap-5">
        <div className="flex items-center gap-1.5">
          <span
            className={`inline-block w-1.5 h-1.5 rounded-full ${
              isError ? "bg-red-500" : "bg-emerald-400 animate-pulse"
            }`}
          />
          <span className="text-[11px] text-gray-500 font-mono">
            {isError ? "API ERROR" : isLoading ? "CONNECTING…" : "LIVE"}
          </span>
        </div>

        {totalRenewable && (
          <span className="text-[11px] font-mono text-gray-500">
            renewable now:{" "}
            <span className="text-emerald-400">{totalRenewable} kW</span>
          </span>
        )}
      </div>

      <div className="flex items-center gap-4">
        <span className="text-[11px] text-gray-600 font-mono">
          {new Date().toLocaleDateString("ja-JP", {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            timeZone: "Asia/Tokyo",
          })}
        </span>
        <LiveClock />
      </div>
    </header>
  );
}
