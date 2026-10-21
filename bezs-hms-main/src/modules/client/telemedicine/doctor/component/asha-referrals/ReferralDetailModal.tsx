"use client";

import React, { useState } from "react";
import {
  X,
  Volume2,
  FileText,
  Activity,
  HeartPulse,
  AlertOctagon,
  PhoneCall,
  Ambulance,
  CheckCircle,
} from "lucide-react";
import type { HighRiskReferralTicket } from "@/modules/server/asha/asha-referral-service";

interface ReferralDetailModalProps {
  referral: HighRiskReferralTicket | null;
  onClose: () => void;
  onUpdateStatus: (ticketId: string, status: HighRiskReferralTicket["status"]) => void;
}

export function ReferralDetailModal({
  referral,
  onClose,
  onUpdateStatus,
}: ReferralDetailModalProps) {
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  if (!referral) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
      <div className="bg-white rounded-3xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-slate-200">
        {/* Header */}
        <div className="p-6 border-b border-slate-100 flex items-start justify-between bg-slate-50/80 rounded-t-3xl">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-black bg-rose-600 text-white">
                {referral.riskLevel} CLINICAL RISK
              </span>
              <span className="text-xs font-bold text-slate-500">
                Ticket: {referral.ticketId}
              </span>
            </div>
            <h2 className="text-xl font-black text-slate-900 mt-1">
              {referral.patientName}
            </h2>
            <p className="text-xs text-slate-600">
              {referral.villageName} • Reported by {referral.workerName}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-700 rounded-full hover:bg-slate-200/60"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          {/* Audio Player Card (bezs-filenest Integration) */}
          <div className="p-4 rounded-2xl bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-blue-600 text-white rounded-xl shadow-xs">
                  <Volume2 className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-sm font-extrabold text-slate-900">
                    Field Visit Voice Recording (Filenest .opus)
                  </div>
                  <div className="text-xs text-slate-600">
                    ASR Source: Sarvam Multilingual Speech Engine
                  </div>
                </div>
              </div>
              <button
                onClick={() => setIsPlayingAudio(!isPlayingAudio)}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-xs ${
                  isPlayingAudio
                    ? "bg-rose-600 text-white animate-pulse"
                    : "bg-blue-600 text-white hover:bg-blue-700"
                }`}
              >
                {isPlayingAudio ? "⏸ Pause Audio" : "▶ Listen to Field Audio"}
              </button>
            </div>
            {isPlayingAudio && (
              <div className="mt-3 p-2.5 rounded-lg bg-white/80 border border-blue-200 text-xs text-blue-900 flex items-center justify-between">
                <span>Streaming from: {referral.voiceAudioUrl || "asha-field-media/voice/visit_audio.opus"}</span>
                <span className="font-bold">0:42 / 1:15</span>
              </div>
            )}
          </div>

          {/* Point-of-Care Vitals Ingestion (open-wearables) */}
          <div>
            <div className="flex items-center gap-2 mb-2 text-xs font-extrabold text-slate-800 uppercase tracking-wider">
              <Activity className="w-4 h-4 text-rose-600" />
              Ingested Vitals (open-wearables BLE Bridge)
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-center">
                <div className="text-[11px] font-semibold text-slate-500">Blood Pressure</div>
                <div className="text-base font-black text-rose-600 mt-0.5">
                  {referral.vitals.systolicBp}/{referral.vitals.diastolicBp}
                </div>
                <div className="text-[10px] text-slate-400">mmHg (LOINC 85354-9)</div>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-center">
                <div className="text-[11px] font-semibold text-slate-500">Hemoglobin</div>
                <div className="text-base font-black text-rose-600 mt-0.5">
                  {referral.vitals.hemoglobin}
                </div>
                <div className="text-[10px] text-slate-400">g/dL (LOINC 718-7)</div>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-center">
                <div className="text-[11px] font-semibold text-slate-500">SpO2 (Pulse Ox)</div>
                <div className="text-base font-black text-blue-600 mt-0.5">
                  {referral.vitals.spo2}%
                </div>
                <div className="text-[10px] text-slate-400">Arterial (LOINC 59408-5)</div>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-center">
                <div className="text-[11px] font-semibold text-slate-500">Body Temp</div>
                <div className="text-base font-black text-amber-600 mt-0.5">
                  {referral.vitals.temperatureC}°C
                </div>
                <div className="text-[10px] text-slate-400">Celsius (LOINC 8310-5)</div>
              </div>
            </div>
          </div>

          {/* AI Clinical Case Notes (langcare-mcp-fhir) */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-700 mb-1.5">
              <FileText className="w-4 h-4 text-emerald-600" />
              AI Clinical Summary (langcare-mcp-fhir)
            </div>
            <p className="text-xs text-slate-700 leading-relaxed">
              {referral.clinicalNotes}
            </p>
          </div>

          {/* Danger Signs List */}
          <div>
            <div className="flex items-center gap-2 mb-2 text-xs font-extrabold text-slate-800 uppercase tracking-wider">
              <AlertOctagon className="w-4 h-4 text-rose-600" />
              Immediate Danger Flags
            </div>
            <div className="space-y-1.5">
              {referral.dangerFlags.map((flag, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-xs font-semibold text-rose-950 flex items-center gap-2"
                >
                  <span className="w-2 h-2 rounded-full bg-rose-600" />
                  {flag}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-slate-100 bg-slate-50/80 rounded-b-3xl flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <a
              href={`tel:${referral.patientPhone}`}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-white text-slate-800 border border-slate-300 hover:bg-slate-100"
            >
              <PhoneCall className="w-3.5 h-3.5 text-blue-600" />
              Call Family
            </a>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                onUpdateStatus(referral.ticketId, "108_AMBULANCE_DISPATCHED");
                onClose();
              }}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-rose-600 text-white hover:bg-rose-700 shadow-sm"
            >
              <Ambulance className="w-4 h-4" />
              Confirm 108 Dispatch
            </button>
            <button
              onClick={() => {
                onUpdateStatus(referral.ticketId, "ARRIVED_AT_PHC");
                onClose();
              }}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-emerald-600 text-white hover:bg-emerald-700 shadow-sm"
            >
              <CheckCircle className="w-4 h-4" />
              Admit to Emergency
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
