import { useOptimize } from "@/hooks/useSchedule";
import type { OptimizeResponse } from "@/types";

interface Props {
  date: string;
  onSuccess?: (result: OptimizeResponse) => void;
}

export default function OptimizeButton({ date, onSuccess }: Props) {
  const { mutate, isPending, isError, error, isSuccess } = useOptimize();

  const handleClick = () => {
    mutate(date, {
      onSuccess: (data) => onSuccess?.(data),
    });
  };

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        onClick={handleClick}
        disabled={isPending}
        className={`
          relative px-4 py-1.5 text-xs font-mono rounded border transition-all
          ${isPending
            ? "border-emerald-700 text-emerald-600 bg-emerald-950/30 cursor-not-allowed"
            : isSuccess
            ? "border-emerald-600 text-emerald-400 bg-emerald-950/20 hover:bg-emerald-950/40"
            : "border-gray-700 text-gray-300 bg-gray-900 hover:border-emerald-700 hover:text-emerald-400"
          }
        `}
      >
        {isPending ? (
          <span className="flex items-center gap-2">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            solving LP…
          </span>
        ) : (
          "run optimizer"
        )}
      </button>
      {isError && (
        <span className="text-[10px] text-red-500 font-mono">
          {(error as Error).message}
        </span>
      )}
    </div>
  );
}
