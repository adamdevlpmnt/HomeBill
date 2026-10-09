import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Skeleton } from "../components/ui/Skeleton";
import { useToast } from "../components/ui/Toast";
import { apiFetch } from "../lib/api";
import { formatCurrency, formatDate, formatConsumption } from "../lib/formatters";
import { Zap, Flame, Droplets, Plus, CheckCircle2 } from "lucide-react";

export const InvoiceDetail: React.FC = () => {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const [showAddInvoice, setShowAddInvoice] = useState(false);

  // Formulaire d'ajout de vraie facture
  const [invEnergy, setInvEnergy] = useState<"sonelgaz" | "water">("sonelgaz");
  const [invCycle, setInvCycle] = useState("2026-Q3");
  const [invNum, setInvNum] = useState("");
  const [invDate, setInvDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [invAmount, setInvAmount] = useState("");

  const { data: estimate, isLoading: isEstimateLoading } = useQuery<any>({
    queryKey: ["billing_estimate"],
    queryFn: () => apiFetch("/api/billing/estimate"),
  });

  const { data: invoices, isLoading: isInvoicesLoading } = useQuery<any[]>({
    queryKey: ["invoices"],
    queryFn: () => apiFetch("/api/invoices"),
  });

  const addInvoiceMutation = useMutation({
    mutationFn: () =>
      apiFetch("/api/invoices", {
        method: "POST",
        body: JSON.stringify({
          energy_group: invEnergy,
          cycle_code: invCycle,
          invoice_number: invNum.trim() || undefined,
          invoice_date: invDate,
          actual_amount: parseFloat(invAmount),
          estimated_amount:
            invEnergy === "sonelgaz"
              ? estimate?.sonelgaz?.net_ttc_central
              : estimate?.water?.net_ttc_central,
        }),
      }),
    onSuccess: () => {
      showToast("Facture réelle enregistrée avec succès !");
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      queryClient.invalidateQueries({ queryKey: ["billing_estimate"] });
      setShowAddInvoice(false);
      setInvAmount("");
      setInvNum("");
    },
    onError: (err: any) => {
      showToast(err.message || "Erreur lors de l'enregistrement", "error");
    },
  });

  return (
    <div className="space-y-4 pb-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-extrabold text-text-primary tracking-tight">
          Factures
        </h1>
        <Button
          size="sm"
          variant="outline"
          onClick={() => setShowAddInvoice(!showAddInvoice)}
          className="text-xs tap-target-44 flex items-center gap-1"
        >
          <Plus className="w-3.5 h-3.5" /> Saisir facture réelle
        </Button>
      </div>

      {/* Formulaire d'enregistrement de facture réelle */}
      {showAddInvoice && (
        <Card elevated className="p-4 space-y-3 border-border animate-in fade-in">
          <h2 className="text-sm font-bold text-text-primary">
            Enregistrer une facture reçue
          </h2>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-[11px] font-semibold text-text-secondary">Énergie</label>
              <select
                value={invEnergy}
                onChange={(e) => setInvEnergy(e.target.value as any)}
                className="w-full bg-surface border border-border rounded-xl p-2 text-xs font-medium text-text-primary mt-1 tap-target-44"
              >
                <option value="sonelgaz">Sonelgaz (Élec + Gaz)</option>
                <option value="water">SEAAL (Eau)</option>
              </select>
            </div>
            <div>
              <label className="text-[11px] font-semibold text-text-secondary">Trimestre</label>
              <input
                type="text"
                value={invCycle}
                onChange={(e) => setInvCycle(e.target.value)}
                placeholder="2026-Q3"
                className="w-full bg-surface border border-border rounded-xl p-2 text-xs font-medium text-text-primary mt-1 tap-target-44"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-[11px] font-semibold text-text-secondary">N° Facture</label>
              <input
                type="text"
                value={invNum}
                onChange={(e) => setInvNum(e.target.value)}
                placeholder="Ex: 571260615440"
                className="w-full bg-surface border border-border rounded-xl p-2 text-xs font-medium text-text-primary mt-1 tap-target-44"
              />
            </div>
            <div>
              <label className="text-[11px] font-semibold text-text-secondary">Date émission</label>
              <input
                type="date"
                value={invDate}
                onChange={(e) => setInvDate(e.target.value)}
                className="w-full bg-surface border border-border rounded-xl p-2 text-xs font-medium text-text-primary mt-1 tap-target-44"
              />
            </div>
          </div>
          <div>
            <label className="text-[11px] font-semibold text-text-secondary">Montant réel TTC (DA)</label>
            <input
              type="number"
              step="any"
              inputMode="decimal"
              value={invAmount}
              onChange={(e) => setInvAmount(e.target.value)}
              placeholder="Ex: 12813.63"
              className="w-full bg-surface border border-border rounded-xl p-2 text-sm font-bold text-text-primary mt-1 tap-target-44"
              required
            />
          </div>
          <div className="flex gap-2 pt-1">
            <Button
              className="flex-1 font-bold text-xs"
              onClick={() => addInvoiceMutation.mutate()}
              loading={addInvoiceMutation.isPending}
              disabled={!invAmount}
            >
              Enregistrer
            </Button>
            <Button
              variant="outline"
              className="text-xs"
              onClick={() => setShowAddInvoice(false)}
            >
              Annuler
            </Button>
          </div>
        </Card>
      )}

      {/* 1. SECTION SONELGAZ (Électricité + Gaz CONJOINTE) : UNIQUEMENT LE NET À PAYER */}
      <Card elevated className="p-4 space-y-3 border-l-4 border-l-[#FACC15]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-surface-elevated text-amber-400 flex items-center gap-1">
              <Zap className="w-4 h-4 text-[#FACC15]" />
              <Flame className="w-4 h-4 text-[#FF7A45]" />
            </span>
            <div>
              <h2 className="text-sm font-bold text-text-primary">
                Facture Sonelgaz (Élec & Gaz)
              </h2>
              {estimate?.start_date && estimate?.end_date && (
                <p className="text-[11px] text-text-secondary">
                  Période : {formatDate(estimate.start_date)} au {formatDate(estimate.end_date)}
                </p>
              )}
            </div>
          </div>
          <span className="text-[11px] px-2 py-0.5 rounded-full bg-surface-elevated text-text-secondary font-medium">
            Facturation conjointe
          </span>
        </div>

        {isEstimateLoading ? (
          <Skeleton className="h-16 w-full" />
        ) : (
          <div className="space-y-3 pt-1">
            {/* Montant Net à payer Sonelgaz */}
            <div className="p-3.5 rounded-2xl bg-surface-elevated/60 border border-border flex items-baseline justify-between">
              <div>
                <span className="text-xs text-text-secondary font-medium block">
                  Net à payer TTC Sonelgaz
                </span>
                <span className="text-2xl sm:text-3xl font-extrabold text-status-success tabular-nums tracking-tight">
                  {formatCurrency(estimate?.sonelgaz?.net_ttc_central)}
                </span>
              </div>
              <span className="text-xs text-text-secondary font-semibold">TTC</span>
            </div>

            {/* Consommations associées */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 rounded-xl bg-surface-elevated/40 border border-border/40">
                <span className="text-text-secondary text-[11px] block flex items-center gap-1">
                  <Zap className="w-3 h-3 text-[#FACC15]" /> Électricité
                </span>
                <span className="font-bold text-text-primary tabular-nums mt-0.5 block">
                  {formatConsumption(estimate?.sonelgaz?.electricity_projected, "kWh")}
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-surface-elevated/40 border border-border/40">
                <span className="text-text-secondary text-[11px] block flex items-center gap-1">
                  <Flame className="w-3 h-3 text-[#FF7A45]" /> Gaz Naturel
                </span>
                <span className="font-bold text-text-primary tabular-nums mt-0.5 block">
                  {formatConsumption(estimate?.sonelgaz?.gas_projected_m3, "m³")}
                </span>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* 2. SECTION SEAAL (Eau & Assainissement) : UNIQUEMENT LE NET À PAYER */}
      <Card elevated className="p-4 space-y-3 border-l-4 border-l-[#38BDF8]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-surface-elevated text-[#38BDF8]">
              <Droplets className="w-4 h-4" />
            </span>
            <div>
              <h2 className="text-sm font-bold text-text-primary">
                Facture SEAAL (Eau & Assainissement)
              </h2>
              {estimate?.water?.baseline_date && estimate?.water?.next_read_date && (
                <p className="text-[11px] text-text-secondary">
                  Période : {formatDate(estimate.water.baseline_date)} au {formatDate(estimate.water.next_read_date)}
                </p>
              )}
            </div>
          </div>
          <span className="text-[11px] px-2 py-0.5 rounded-full bg-surface-elevated text-text-secondary font-medium">
            SEAAL Alger
          </span>
        </div>

        {isEstimateLoading ? (
          <Skeleton className="h-16 w-full" />
        ) : (
          <div className="space-y-3 pt-1">
            {/* Montant Net à payer SEAAL */}
            <div className="p-3.5 rounded-2xl bg-surface-elevated/60 border border-border flex items-baseline justify-between">
              <div>
                <span className="text-xs text-text-secondary font-medium block">
                  Net à payer TTC SEAAL
                </span>
                <span className="text-2xl sm:text-3xl font-extrabold text-[#38BDF8] tabular-nums tracking-tight">
                  {formatCurrency(estimate?.water?.net_ttc_central)}
                </span>
              </div>
              <span className="text-xs text-text-secondary font-semibold">TTC</span>
            </div>

            {/* Consommation associée */}
            <div className="p-2.5 rounded-xl bg-surface-elevated/40 border border-border/40 text-xs flex justify-between items-center">
              <span className="text-text-secondary text-[11px] flex items-center gap-1">
                <Droplets className="w-3 h-3 text-[#38BDF8]" /> Eau consommée
              </span>
              <span className="font-bold text-text-primary tabular-nums">
                {formatConsumption(estimate?.water?.water_projected_m3, "m³")}
              </span>
            </div>
          </div>
        )}
      </Card>

      {/* 3. HISTORIQUE DES FACTURES RÉELLES & ÉCARTS */}
      <div className="space-y-2 pt-2">
        <h2 className="text-xs font-bold uppercase tracking-wider text-text-secondary px-1">
          Historique des factures réelles & écarts
        </h2>

        {isInvoicesLoading ? (
          <Skeleton className="h-24 w-full" />
        ) : invoices && invoices.length > 0 ? (
          <div className="space-y-2">
            {invoices.map((inv) => (
              <Card key={inv.id} className="p-3.5 space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-sm font-bold text-text-primary">
                      {inv.energy_group === "sonelgaz" ? "Sonelgaz" : "SEAAL"} • {inv.cycle_code}
                    </span>
                    <p className="text-xs text-text-secondary">
                      {inv.invoice_number && `N° ${inv.invoice_number} • `}
                      {formatDate(inv.invoice_date)}
                    </p>
                  </div>
                  <span className="text-base font-extrabold text-text-primary tabular-nums">
                    {formatCurrency(inv.actual_amount)}
                  </span>
                </div>

                {inv.variance_amount !== null && (
                  <div className="flex items-center justify-between text-xs pt-1 border-t border-border/40">
                    <span className="text-text-secondary">
                      Estimation : {formatCurrency(inv.estimated_amount)}
                    </span>
                    <span
                      className={
                        Math.abs(Number(inv.variance_pct || 0)) <= 1.0
                          ? "text-status-success font-semibold flex items-center gap-1"
                          : "text-amber-500 font-semibold"
                      }
                    >
                      {Math.abs(Number(inv.variance_pct || 0)) <= 1.0 && <CheckCircle2 className="w-3.5 h-3.5" />}
                      Écart : {inv.variance_pct > 0 ? `+${inv.variance_pct}%` : `${inv.variance_pct}%`} ({formatCurrency(inv.variance_amount)})
                    </span>
                  </div>
                )}
              </Card>
            ))}
          </div>
        ) : (
          <Card className="text-center py-6 text-text-secondary text-sm">
            Aucune facture réelle enregistrée.
          </Card>
        )}
      </div>
    </div>
  );
};
