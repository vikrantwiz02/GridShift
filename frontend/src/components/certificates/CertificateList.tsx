import type { Certificate } from "@/types";

interface Props {
  certs: Certificate[];
  selectedSeq: number | null;
  onSelect: (seq: number) => void;
}

export default function CertificateList({ certs, selectedSeq, onSelect }: Props) {
  if (certs.length === 0) {
    return (
      <div className="text-sm text-gray-600 py-8 text-center">
        No certificates yet — run the optimizer to generate one.
      </div>
    );
  }

  return (
    <div className="overflow-y-auto max-h-[600px]">
      {certs.map((cert) => {
        const isSelected = cert.seq === selectedSeq;
        const issued = new Date(cert.issued_at).toLocaleString("ja-JP", {
          timeZone: "Asia/Tokyo",
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
        });
        return (
          <button
            key={cert.seq}
            onClick={() => onSelect(cert.seq)}
            className={`w-full text-left px-4 py-3 border-b border-gray-800 flex items-start gap-3 hover:bg-gray-800/50 transition-colors ${
              isSelected ? "bg-gray-800" : ""
            }`}
          >
            <span className="text-xs text-gray-600 w-8 shrink-0 pt-0.5">#{cert.seq}</span>
            <div className="min-w-0">
              <p className="text-xs font-mono text-gray-400 truncate">{cert.cert_hash.slice(0, 20)}…</p>
              <p className="text-[10px] text-gray-600 mt-0.5">{issued} JST</p>
            </div>
          </button>
        );
      })}
    </div>
  );
}
