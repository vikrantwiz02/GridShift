import type { Certificate } from "@/types";

interface Props {
  cert: Certificate;
  prevCert: Certificate | null;
}

function HashField({
  label,
  value,
  compareWith,
  compareLabel,
}: {
  label: string;
  value: string;
  compareWith?: string;
  compareLabel?: string;
}) {
  const matched = compareWith !== undefined ? value === compareWith : undefined;

  return (
    <div className="py-2.5 border-b border-gray-800/60 last:border-0">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] font-mono text-gray-600 uppercase tracking-wider">{label}</span>
        {matched !== undefined && (
          <span
            className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
              matched
                ? "text-emerald-400 bg-emerald-950/40"
                : "text-red-400 bg-red-950/40"
            }`}
          >
            {matched ? `✓ links to ${compareLabel}` : `✗ broken — expected ${compareLabel}`}
          </span>
        )}
      </div>
      <p className="font-mono text-[11px] text-gray-400 break-all leading-relaxed">
        {value.slice(0, 32)}
        <span className="text-gray-300">{value.slice(32)}</span>
      </p>
    </div>
  );
}

export default function CertificateDetail({ cert, prevCert }: Props) {
  let payload: Record<string, unknown> = {};
  try {
    payload = JSON.parse(cert.data_json);
  } catch {}

  const issuedAt = new Date(cert.issued_at).toLocaleString("ja-JP", {
    timeZone: "Asia/Tokyo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  return (
    <div className="bg-gray-900/60 rounded-lg border border-gray-800/60 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-800/60 flex items-center justify-between bg-gray-950/40">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-gray-600">seq</span>
          <span className="text-sm font-mono font-semibold text-gray-200">#{cert.seq}</span>
        </div>
        <span className="text-[10px] font-mono text-gray-600">{issuedAt} JST</span>
      </div>

      <div className="px-4 divide-y divide-gray-800/40">
        <HashField label="cert_hash" value={cert.cert_hash} />
        <HashField
          label="prev_hash"
          value={cert.prev_hash}
          compareWith={prevCert?.cert_hash}
          compareLabel={prevCert ? `#${prevCert.seq} cert_hash` : undefined}
        />
        <HashField label="payload_hash" value={cert.payload_hash} />
      </div>

      <div className="px-4 py-3 border-t border-gray-800/60">
        <p className="text-[10px] font-mono text-gray-600 uppercase tracking-wider mb-2">payload</p>
        <pre className="bg-gray-950/60 rounded px-3 py-2.5 text-[11px] font-mono text-gray-400 overflow-x-auto leading-relaxed">
          {JSON.stringify(payload, null, 2)}
        </pre>
      </div>
    </div>
  );
}
