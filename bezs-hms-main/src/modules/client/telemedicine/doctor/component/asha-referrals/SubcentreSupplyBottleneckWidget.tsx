"use client";

import React from "react";
import {
  PackageX,
  Check,
  Mic,
  MapPin,
  Clock,
  Sparkles,
} from "lucide-react";
import type { SupplyStockoutAlert } from "@/modules/server/asha/asha-referral-service";

interface SubcentreSupplyBottleneckWidgetProps {
  supplies: SupplyStockoutAlert[];
  onApproveDispatch: (alertId: string) => void;
}

export function SubcentreSupplyBottleneckWidget({
  supplies,
  onApproveDispatch,
}: SubcentreSupplyBottleneckWidgetProps) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
      <div className="flex items-center justify-between pb-3.5 border-b border-slate-100 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <PackageX className="w-5 h-5 text-amber-600" />
            <h3 className="font-extrabold text-base text-slate-900">
              Sub-Centre Supply & Kit Bottlenecks
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Voice-flagged stockouts aggregated from ASHAs & ANMs at PHC Pharmacy Level
          </p>
        </div>
        <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800">
          {supplies.filter((s) => s.approvalStatus === "PENDING_APPROVAL").length} Pending Requests
        </span>
      </div>

      <div className="space-y-3">
        {supplies.map((item) => {
          const isCritical = item.stockStatus === "CRITICAL_STOCKOUT";
          const isApproved = item.approvalStatus === "APPROVED_DISPATCHED";

          return (
            <div
              key={item.alertId}
              className={`p-3.5 rounded-xl border transition-all ${
                isApproved
                  ? "bg-slate-50 border-slate-200 opacity-75"
                  : isCritical
                  ? "bg-rose-50/60 border-rose-200"
                  : "bg-amber-50/60 border-amber-200"
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-sm text-slate-900">
                      {item.itemName}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-extrabold ${
                        isCritical
                          ? "bg-rose-100 text-rose-800 border border-rose-300"
                          : "bg-amber-100 text-amber-800 border border-amber-300"
                      }`}
                    >
                      {item.stockStatus.replace("_", " ")}
                    </span>
                    <span className="text-xs font-semibold text-slate-600">
                      Current Stock: <strong className="text-rose-600">{item.currentStock}</strong> | Req: <strong>{item.quantityRequested}</strong>
                    </span>
                  </div>

                  <div className="flex items-center gap-3 text-xs text-slate-600 mt-1 flex-wrap">
                    <span className="flex items-center gap-1 font-medium">
                      <MapPin className="w-3 h-3 text-blue-600" />
                      {item.subcentreName} (LGD: {item.villageLgdCode})
                    </span>
                    <span className="text-slate-500 font-medium">
                      Reported by: <strong>{item.workerName}</strong>
                    </span>
                  </div>
                </div>

                <div className="self-end sm:self-center">
                  {isApproved ? (
                    <span className="inline-flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-bold bg-emerald-100 text-emerald-800">
                      <Check className="w-3.5 h-3.5" /> Dispatched
                    </span>
                  ) : (
                    <button
                      onClick={() => onApproveDispatch(item.alertId)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 text-white hover:bg-emerald-700 shadow-sm"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      Approve & Dispatch Kit
                    </button>
                  )}
                </div>
              </div>

              {/* Voice Command Snippet */}
              {item.reportedViaVoice && item.voiceTranscriptSnippet && (
                <div className="mt-2.5 p-2 rounded-lg bg-white/90 border border-slate-200/80 text-xs text-slate-700 italic flex items-center gap-2">
                  <Mic className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                  <span>&quot;{item.voiceTranscriptSnippet}&quot;</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
