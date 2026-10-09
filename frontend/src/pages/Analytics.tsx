import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card } from "../components/ui/Card";
import { SegmentedControl, SegmentOption } from "../components/ui/SegmentedControl";
import { EnergyPill, EnergyFilterKey } from "../components/ui/EnergyPill";
import { Skeleton } from "../components/ui/Skeleton";
import { apiFetch } from "../lib/api";
import { formatNumber, formatCurrency } from "../lib/formatters";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

type PeriodType = "week" | "month" | "quarter" | "year";

export const Analytics: React.FC = () => {
  const [period, setPeriod] = useState<PeriodType>("week");
  const [activeEnergy, setActiveEnergy] = useState<EnergyFilterKey>("electricity");
  const [metricMode, setMetricMode] = useState<"consumption" | "cost">("consumption");

  const periodOptions: SegmentOption<PeriodType>[] = [
    { value: "week", label: "Semaine" },
    { value: "month", label: "Mois" },
    { value: "quarter", label: "Trimestre" },
    { value: "year", label: "Année" },
  ];

  const { data: timeseries, isLoading } = useQuery<any[]>({
    queryKey: ["analytics", { period }],
    queryFn: () => apiFetch(`/api/analytics/timeseries?period=${period}`),
  });

  const getEnergyColor = () => {
    if (activeEnergy === "electricity") return "#FACC15";
    if (activeEnergy === "gas") return "#FF7A45";
    if (activeEnergy === "water") return "#38BDF8";
    return "#38BDF8";
  };

  const getEnergyUnit = () => {
    if (activeEnergy === "electricity") return "kWh";
    if (activeEnergy === "gas") return "m³";
    if (activeEnergy === "water") return "m³";
    return "";
  };

  const getDataKey = () => {
    if (metricMode === "cost") {
      if (activeEnergy === "electricity") return "electricity_cost";
      if (activeEnergy === "gas") return "gas_cost";
      if (activeEnergy === "water") return "water_cost";
      return "total_cost";
    }
    if (activeEnergy === "electricity") return "electricity_kwh";
    if (activeEnergy === "gas") return "gas_m3";
    if (activeEnergy === "water") return "water_m3";
    return "electricity_kwh";
  };

  // Calcul d'une moyenne mobile 4 périodes
  const chartData = (timeseries || []).map((item, idx, arr) => {
    const key = getDataKey();
    let movingAvg = Number(item[key] || 0);
    if (idx >= 3) {
      const sum4 =
        Number(arr[idx][key] || 0) +
        Number(arr[idx - 1][key] || 0) +
        Number(arr[idx - 2][key] || 0) +
        Number(arr[idx - 3][key] || 0);
      movingAvg = Math.round((sum4 / 4) * 10) / 10;
    }
    return {
      ...item,
      chartValue: Number(item[key] || 0),
      movingAvg,
    };
  });

  const activeColor = getEnergyColor();

  return (
    <div className="space-y-4 pb-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-extrabold text-text-primary tracking-tight">
          Analyses de consommation
        </h1>
      </div>

      {/* 1. Sélecteur segmenté : Semaine / Mois / Trimestre / Année */}
      <SegmentedControl
        options={periodOptions}
        value={period}
        onChange={setPeriod}
      />

      {/* 2. Puces de filtrage par énergie */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
        <EnergyPill
          energy="electricity"
          active={activeEnergy === "electricity"}
          onClick={() => setActiveEnergy("electricity")}
        />
        <EnergyPill
          energy="gas"
          active={activeEnergy === "gas"}
          onClick={() => setActiveEnergy("gas")}
        />
        <EnergyPill
          energy="water"
          active={activeEnergy === "water"}
          onClick={() => setActiveEnergy("water")}
        />
      </div>

      {/* Bascule Consommation / Coût pour la vue Année */}
      {period === "year" && (
        <div className="flex justify-end">
          <div className="inline-flex rounded-lg border border-border p-0.5 bg-surface text-xs font-medium">
            <button
              onClick={() => setMetricMode("consumption")}
              className={`px-3 py-1 rounded-md transition-colors ${metricMode === "consumption" ? "bg-surface-elevated text-text-primary font-bold shadow-sm" : "text-text-secondary"}`}
            >
              Consommation
            </button>
            <button
              onClick={() => setMetricMode("cost")}
              className={`px-3 py-1 rounded-md transition-colors ${metricMode === "cost" ? "bg-surface-elevated text-text-primary font-bold shadow-sm" : "text-text-secondary"}`}
            >
              Coût (DA)
            </button>
          </div>
        </div>
      )}

      {/* Graphique Principal */}
      <Card elevated className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-text-secondary">
            Évolution {period === "week" ? "par semaine" : period === "month" ? "par mois" : period === "quarter" ? "par trimestre" : "par an"}
          </span>
          <span className="text-xs font-semibold text-text-secondary">
            Unité : {metricMode === "cost" ? "DA" : getEnergyUnit()}
          </span>
        </div>

        {isLoading ? (
          <Skeleton className="h-64 w-full" />
        ) : chartData.length > 0 ? (
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27325A" opacity={0.3} vertical={false} />
                <XAxis dataKey="label" stroke="#8A94B8" fontSize={11} tickLine={false} />
                <YAxis stroke="#8A94B8" fontSize={11} tickLine={false} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="p-2.5 rounded-xl bg-surface border border-border shadow-floating text-xs">
                          <p className="font-bold text-text-primary mb-1">{data.label}</p>
                          <p style={{ color: activeColor }} className="font-semibold tabular-nums">
                            {metricMode === "cost" ? formatCurrency(data.chartValue) : `${formatNumber(data.chartValue)} ${getEnergyUnit()}`}
                          </p>
                          {period === "week" && data.movingAvg > 0 && (
                            <p className="text-text-secondary text-[10px] mt-0.5">
                              Moyenne 4 sem. : {formatNumber(data.movingAvg)} {getEnergyUnit()}
                            </p>
                          )}
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="chartValue" fill={activeColor} radius={[6, 6, 0, 0]} />
                {period === "week" && (
                  <Line
                    type="monotone"
                    dataKey="movingAvg"
                    stroke="#E8ECF8"
                    strokeWidth={2}
                    dot={false}
                    name="Moyenne mobile"
                  />
                )}
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-64 flex items-center justify-center text-text-secondary text-sm">
            Aucune donnée pour cette période.
          </div>
        )}
      </Card>

      {/* Graphique secondaire : Taux Journalier (pour repérer les dérives) */}
      <Card className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-text-secondary">
            Taux journalier moyen ({getEnergyUnit()}/jour)
          </span>
        </div>

        {isLoading ? (
          <Skeleton className="h-44 w-full" />
        ) : chartData.length > 0 ? (
          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={chartData.map((d) => ({
                  ...d,
                  rate:
                    activeEnergy === "electricity"
                      ? Number(d.daily_rate_elec || 0)
                      : activeEnergy === "gas"
                      ? Number(d.daily_rate_gas_m3 || 0)
                      : Number(d.daily_rate_water || 0),
                }))}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#27325A" opacity={0.3} vertical={false} />
                <XAxis dataKey="label" stroke="#8A94B8" fontSize={11} tickLine={false} />
                <YAxis stroke="#8A94B8" fontSize={11} tickLine={false} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="p-2.5 rounded-xl bg-surface border border-border shadow-floating text-xs">
                          <p className="font-bold text-text-primary mb-1">{data.label}</p>
                          <p style={{ color: activeColor }} className="font-semibold tabular-nums">
                            {formatNumber(data.rate, 2)} {getEnergyUnit()}/jour
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="rate"
                  stroke={activeColor}
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: activeColor }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : null}
      </Card>
    </div>
  );
};
