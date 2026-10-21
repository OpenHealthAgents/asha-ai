"use client";

import React from "react";
import {
  AlertTriangle,
  Ambulance,
  CheckCircle,
  Clock,
  Eye,
  FileAudio,
  MapPin,
  Phone,
  User,
  HeartPulse,
} from "lucide-react";
import type { HighRiskReferralTicket } from "@/modules/server/asha/asha-referral-service";

interface HighRiskReferralQueueProps {
  referrals: HighRiskReferralTicket[];
  onSelectReferral: (referral: HighRiskReferralTicket) => void;
  onUpdateStatus: (ticketId: string, status: HighRiskReferralTicket["status"]) => void;
}

export function HighRiskReferralQueue({
  referrals,
  onSelectReferral,
  onUpdateStatus,
}: HighRiskReferralQueueProps) {
  if (referrals.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center bg-white rounded-xl border border-slate-200">
        <CheckCircle className="w-12 h-12 text-emerald-500 mb-3" />
        <h3 className="text-base font-semibold text-slate-800">No Active High-Risk Referrals</h3>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          All village triage cases in this PHC block are currently triaged and within routine parameters.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {referrals.map((item) => {
        const isDispatched = item.status === "108_AMBULANCE_DISPATCHED";
        const isArrived = item.status === "ARRIVED_AT_PHC";

        return (
          <div
            key={item.ticketId}
            className={`p-5 rounded-2xl border transition-all ${
              isDispatched
                ? "bg-rose-50/70 border-rose-300 shadow-sm"
                : isArrived
                ? "bg-emerald-50/60 border-emerald-300"
                : "bg-amber-50/50 border-amber-300"
            }`}
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              {/* Left Column: Patient & Category */}
              <div className="flex items-start gap-3.5">
                <div
                  className={`p-2.5 rounded-xl text-white ${
                    isDispatched ? "bg-rose-600" : "bg-amber-600"
                  }`}
                >
                  <AlertTriangle className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-extrabold text-base text-slate-900">
                      {item.patientName}
                    </span>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-200">
                      {item.riskLevel} RISK
                    </span>
                    <span className="px-2 py-0.5 rounded-md text-xs font-semibold bg-slate-100 text-slate-700">
                      {item.category.replace("_", " ")}
                    </span>
                  </div>

                  <div className="flex items-center gap-4 text-xs text-slate-600 mt-1.5 flex-wrap">
                    <span className="flex items-center gap-1 font-medium">
                      <MapPin className="w-3.5 h-3.5 text-blue-600" />
                      {item.villageName} (LGD: {item.villageLgdCode})
                    </span>
                    <span className="flex items-center gap-1 font-medium">
                      <Phone className="w-3.5 h-3.5 text-slate-500" />
                      {item.patientPhone}
                    </span>
                    <span className="flex items-center gap-1 text-slate-700 font-semibold">
                      <User className="w-3.5 h-3.5 text-emerald-600" />
                      Reported by: {item.workerName}
                    </span>
                  </div>
                </div>
              </div>

              {/* Status Badge & Actions */}
              <div className="flex items-center gap-2 flex-wrap self-end md:self-center">
                <button
                  onClick={() => onSelectReferral(item)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-white text-slate-800 border border-slate-300 hover:bg-slate-50 shadow-sm"
                >
                  <Eye className="w-3.5 h-3.5 text-blue-600" />
                  View Case & Audio
                </button>

                {!isArrived && (
                  <button
                    onClick={() => onUpdateStatus(item.ticketId, "ARRIVED_AT_PHC")}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 text-white hover:bg-emerald-700 shadow-sm"
                  >
                    <CheckCircle className="w-3.5 h-3.5" />
                    Admit to PHC
                  </button>
                )}

                {!isDispatched && !isArrived && (
                  <button
                    onClick={() => onUpdateStatus(item.ticketId, "108_AMBULANCE_DISPATCHED")}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-rose-600 text-white hover:bg-rose-700 shadow-sm"
                  >
                    <Ambulance className="w-3.5 h-3.5" />
                    Dispatch 108
                  </button>
                )}
              </div>
            </div>

            {/* Danger Flags Pill List */}
            <div className="mt-3.5 pt-3 border-t border-slate-200/70">
              <div className="text-xs font-bold text-slate-700 mb-1.5">Detected Danger Signs:</div>
              <div className="flex flex-wrap gap-2">
                {item.dangerFlags.map((flag, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-white text-rose-900 border border-rose-200 shadow-2xs"
                  >
                    • {flag}
                  </span>
                ))}
              </div>
            </div>

            {/* Vitals Summary Strip */}
            <div className="mt-3 flex items-center gap-4 text-xs font-semibold text-slate-800 bg-white/80 p-2.5 rounded-xl border border-slate-200/70">
              <span className="flex items-center gap-1 text-rose-600">
                <HeartPulse className="w-4 h-4" />
                Vitals:
              </span>
              {item.vitals.systolicBp && (
                <span className="px-2 py-0.5 rounded bg-slate-100">
                  BP: <strong className="text-rose-700">{item.vitals.systolicBp}/{item.vitals.diastolicBp}</strong> mmHg
                </span>
              )}
              {item.vitals.hemoglobin && (
                <span className="px-2 py-0.5 rounded bg-slate-100">
                  Hb: <strong className="text-rose-700">{item.vitals.hemoglobin}</strong> g/dL
                </span>
              )}
              {item.vitals.spo2 && (
                <span className="px-2 py-0.5 rounded bg-slate-100">
                  SpO2: <strong className="text-blue-700">{item.vitals.spo2}%</strong>
                </span>
              )}
              {item.vitals.temperatureC && (
                <span className="px-2 py-0.5 rounded bg-slate-100">
                  Temp: <strong className="text-amber-700">{item.vitals.temperatureC}°C</strong>
                </span>
              )}
              <span className="ml-auto text-[11px] text-slate-500 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {new Date(item.escalatedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
