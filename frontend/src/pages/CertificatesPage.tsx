import { useState } from "react";
import { useCertificate, useCertificates, useChainVerify } from "@/hooks/useCertificates";
import CertificateList from "@/components/certificates/CertificateList";
import CertificateDetail from "@/components/certificates/CertificateDetail";

export default function CertificatesPage() {
  const [selectedSeq, setSelectedSeq] = useState<number | null>(null);
  const { data: certs = [], isLoading } = useCertificates(50);
  const { data: selected } = useCertificate(selectedSeq);
  const { data: verifyResult, refetch: runVerify, isFetching: verifying } = useChainVerify();

  const prevCert =
    (selected && certs.find((c) => c.seq === selected.seq - 1)) ?? null;

  return (
    <div className="max-w-5xl space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-base font-semibold text-gray-200">
          Energy Attribution Chain
        </h1>
        <div className="flex items-center gap-3">
          {verifyResult && (
            <span
              className={`text-xs px-2 py-1 rounded-md ${
                verifyResult.valid
                  ? "bg-emerald-900/40 text-emerald-400"
                  : "bg-red-900/40 text-red-400"
              }`}
            >
              {verifyResult.message}
            </span>
          )}
          <button
            onClick={() => runVerify()}
            disabled={verifying}
            className="text-xs px-3 py-1.5 rounded-lg border border-gray-700 text-gray-400 hover:text-gray-200 hover:border-gray-600 disabled:opacity-50 transition-colors"
          >
            {verifying ? "Verifying…" : "Verify chain"}
          </button>
        </div>
      </div>

      <p className="text-xs text-gray-600">
        Each entry is a SHA-256 hash-chain record of one optimization run. Any
        modification to a historical record breaks the chain at that sequence number.
      </p>

      <div className="grid grid-cols-5 gap-4">
        <div className="col-span-2 bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
          {isLoading ? (
            <div className="h-64 animate-pulse" />
          ) : (
            <CertificateList
              certs={certs}
              selectedSeq={selectedSeq}
              onSelect={setSelectedSeq}
            />
          )}
        </div>

        <div className="col-span-3">
          {selected ? (
            <CertificateDetail cert={selected} prevCert={prevCert} />
          ) : (
            <div className="h-full flex items-center justify-center text-sm text-gray-600">
              Select a certificate to inspect its hash chain linkage
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
