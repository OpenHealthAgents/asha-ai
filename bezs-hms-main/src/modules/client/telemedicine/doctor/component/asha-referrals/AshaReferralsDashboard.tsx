"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  Ambulance,
  Building2,
  Clock,
  PackageX,
  RefreshCw,
  ShieldAlert,
} from "lucide-react";
import type {
  HighRiskReferralTicket,
  SupplyStockoutAlert,
} from "@/modules/server/asha/asha-referral-service";
import { HighRiskReferralQueue } from "./HighRiskReferralQueue";
import { SubcentreSupplyBottleneckWidget } from "./SubcentreSupplyBottleneckWidget";
import { ReferralDetailModal } from "./ReferralDetailModal";

interface AshaReferralsDashboardProps {
  initialReferrals: HighRiskReferralTicket[];
  initialSupplies: SupplyStockoutAlert[];
}

export function AshaReferralsDashboard({
  initialReferrals,
  initialSupplies,
}: AshaReferralsDashboardProps) {
  const [referrals, setReferrals] = useState<HighRiskReferralTicket[]>(initialReferrals);
  const [supplies, setSupplies] = useState<SupplyStockoutAlert[]>(initialSupplies);
  const [selectedReferral, setSelectedReferral] = useState<HighRiskReferralTicket | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleUpdateStatus = (ticketId: string, newStatus: HighRiskReferralTicket["status"]) => {
    setReferrals((prev) =>
      prev.map((r) => (r.ticketId === ticketId ? { ...r, status: newStatus } : r))
    );
  };

  const handleApproveDispatch = (alertId: string) => {
    setSupplies((prev) =>
      prev.map((s) => (s.alertId === alertId ? { ...s, approvalStatus: "APPROVED_DISPATCHED" } : s))
    );
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const res = await fetch("/api/asha-referrals/list");
      if (res.ok) {
        const data = await res.json();
        setReferrals(data.referrals || []);
        setSupplies(data.supplyStockouts || []);
      }
    } catch (_) {}
    setIsRefreshing(false);
  };

  const totalReferrals = referrals.length;
  const ambulanceDispatched = referrals.filter((r) => r.status === "108_AMBULANCE_DISPATCHED").length;
  const pendingArrivals = referrals.filter((r) => r.status === "PENDING_ARRIVAL").length;
  const criticalStockouts = supplies.filter((s) => s.stockStatus === "CRITICAL_STOCKOUT").length;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 p-6 rounded-3xl text-white shadow-lg">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-white/20">
              <Building2 className="w-5 h-5 text-blue-200" />
            </span>
            <span className="text-xs font-black uppercase tracking-wider text-blue-300">
              National Health Mission • Primary Health Centre Command Center
            </span>
          </div>
          <h1 className="text-2xl font-black mt-2">
            Frontline ASHA Referrals & Triage Command
          </h1>
          <p className="text-xs text-blue-200 mt-1 max-w-2xl">
            Live village referrals triage queue connecting DrGodly mobile clients, bezs-filenest audio,
            open-wearables vitals, and PHC emergency intake.
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="self-start md:self-center flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold bg-white/10 hover:bg-white/20 border border-white/20 transition-all text-white"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`} />
          {isRefreshing ? "Syncing..." : "Live Refresh"}
        </button>
      </div>

      {/* KPI Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total High-Risk Referrals */}
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 text-xs font-bold">
            <span>High-Risk Referrals</span>
            <ShieldAlert className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-black text-rose-600 mt-2">{totalReferrals}</div>
          <div className="text-[11px] text-slate-500 mt-1">Village beats active today</div>
        </div>

        {/* 108 Ambulance Dispatched */}
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 text-xs font-bold">
            <span>108 Ambulance En Route</span>
            <Ambulance className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-black text-rose-600 mt-2">{ambulanceDispatched}</div>
          <div className="text-[11px] text-slate-500 mt-1">Pre-eclampsia & fetal distress</div>
        </div>

        {/* Pending PHC Arrivals */}
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 text-xs font-bold">
            <span>Pending PHC Arrivals</span>
            <Clock className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-black text-amber-600 mt-2">{pendingArrivals}</div>
          <div className="text-[11px] text-slate-500 mt-1">48h verification countdown</div>
        </div>

        {/* Sub-Centre Supply Stockouts */}
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 text-xs font-bold">
            <span>Supply Stockouts</span>
            <PackageX className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-black text-amber-600 mt-2">{criticalStockouts}</div>
          <div className="text-[11px] text-slate-500 mt-1">IFA, ORS, UPT kit requests</div>
        </div>
      </div>

      {/* Main Content Grid: Referrals Queue (Left) + Supply Bottlenecks (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-black text-slate-900 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-rose-600" />
              Incoming Village Referral Queue
            </h2>
            <span className="text-xs text-slate-500">Live Kestra Event Stream</span>
          </div>
          <HighRiskReferralQueue
            referrals={referrals}
            onSelectReferral={(ref) => setSelectedReferral(ref)}
            onUpdateStatus={handleUpdateStatus}
          />
        </div>

        <div className="space-y-4">
          <SubcentreSupplyBottleneckWidget
            supplies={supplies}
            onApproveDispatch={handleApproveDispatch}
          />
        </div>
      </div>

      {/* Case Detail Modal */}
      <ReferralDetailModal
        referral={selectedReferral}
        onClose={() => setSelectedReferral(null)}
        onUpdateStatus={handleUpdateStatus}
      />
    </div>
  );
}
