import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Skeleton } from "../components/ui/Skeleton";
import { Button } from "../components/ui/Button";
import { ModalSheet } from "../components/ui/ModalSheet";
import { useToast } from "../components/ui/Toast";
import { SparklineArea } from "../components/charts/SparklineArea";
import { SaisieModal } from "../components/saisie/SaisieModal";
import { apiFetch } from "../lib/api";
import {
  formatCurrency,
  formatConsumption,
  formatDate,
  formatPercent,
  formatNumber,
} from "../lib/formatters";
import {
  Zap,
  Flame,
  Droplets,
  Calendar,
  TrendingUp,
  TrendingDown,
  ShieldCheck,
  Plus,
  Pencil,
  Trash2,
  AlertTriangle,
} from "lucide-react";

export const Home: React.FC = () => {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const [isSaisieOpen, setIsSaisieOpen] = useState(false);

  // État d'édition d'un relevé
  const [editingReading, setEditingReading] = useState<any | null>(null);
  const [editDate, setEditDate] = useState("");
  const [editIndex, setEditIndex] = useState("");
  const [editNote, setEditNote] = useState("");

  // État de suppression d'un relevé
  const [deletingReading, setDeletingReading] = useState<any | null>(null);

  // 1. Estimation du trimestre
  const { data: estimate, isLoading: isEstimateLoading } = useQuery<any>({
    queryKey: ["billing_estimate"],
    queryFn: () => apiFetch("/api/billing/estimate"),
  });

  // 2. Sparklines
  const { data: sparklines } = useQuery<any>({
    queryKey: ["sparklines"],
    queryFn: () => apiFetch("/api/analytics/sparklines"),
  });

  // 3. Derniers relevés
  const { data: readings, isLoading: isReadingsLoading } = useQuery<any[]>({
    queryKey: ["readings", { limit: 10 }],
    queryFn: () => apiFetch("/api/readings?limit=10"),
  });

  // Mutation modification d'un relevé
  const updateReadingMutation = useMutation({
    mutationFn: () =>
      apiFetch(`/api/readings/${editingReading.id}`, {
        method: "PUT",
        body: JSON.stringify({
          read_at: editDate,
          index_value: parseFloat(editIndex),
          note: editNote.trim() || undefined,
        }),
      }),
    onSuccess: () => {
      showToast("Relevé modifié avec succès !");
      queryClient.invalidateQueries({ queryKey: ["readings"] });
      queryClient.invalidateQueries({ queryKey: ["billing_estimate"] });
      queryClient.invalidateQueries({ queryKey: ["sparklines"] });
      setEditingReading(null);
    },
    onError: (err: any) => {
      showToast(err.message || "Erreur lors de la modification", "error");
    },
  });

  // Mutation suppression d'un relevé
  const deleteReadingMutation = useMutation({
    mutationFn: (id: number) =>
      apiFetch(`/api/readings/${id}`, {
        method: "DELETE",
      }),
    onSuccess: () => {
      showToast("Relevé supprimé avec succès !");
      queryClient.invalidateQueries({ queryKey: ["readings"] });
      queryClient.invalidateQueries({ queryKey: ["billing_estimate"] });
      queryClient.invalidateQueries({ queryKey: ["sparklines"] });
      setDeletingReading(null);
    },
    onError: (err: any) => {
      showToast(err.message || "Erreur lors de la suppression", "error");
    },
  });

  const handleOpenEdit = (r: any) => {
    setEditingReading(r);
    setEditDate(r.read_at);
    setEditIndex(String(r.index_value));
    setEditNote(r.note || "");
  };

  // Vérifier si un relevé a été fait cette semaine
  const hasReadingThisWeek = () => {
    if (!readings || readings.length === 0) return false;
    const latestDate = new Date(readings[0].read_at);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - latestDate.getTime()) / (1000 * 3600 * 24));
    return diffDays < 7;
  };

  const showReminder = !hasReadingThisWeek();

  return (
    <div className="space-y-4 pb-6">
      {/* Bandeau de rappel du vendredi si aucun relevé cette semaine */}
      {showReminder && (
        <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-between gap-3 animate-in fade-in">
          <div className="flex items-center gap-2.5">
            <span className="p-2 rounded-xl bg-amber-500/20 text-amber-500 flex-shrink-0">
              <Calendar className="w-5 h-5" />
            </span>
            <div>
              <p className="text-xs font-bold text-text-primary">
                Relevé du vendredi
              </p>
              <p className="text-[11px] text-text-secondary">
                Aucun relevé enregistré ces 7 derniers jours.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setIsSaisieOpen(true)}
            className="px-3 py-1.5 rounded-xl bg-amber-500 text-slate-950 text-xs font-bold shadow-sm active:scale-95 transition-transform flex items-center gap-1 tap-target-44 flex-shrink-0"
          >
            <Plus className="w-3.5 h-3.5" /> Relever
          </button>
        </div>
      )}

      {/* CARTE HÉRO : Facture estimée du trimestre en cours */}
      <Card elevated className="space-y-4 relative overflow-hidden">
        {/* En-tête de la carte */}
        <div className="flex items-center justify-between">
          <div className="flex flex-col">
            <span className="text-xs font-bold uppercase tracking-wider text-text-secondary">
              Facture estimée • {estimate?.cycle_code || "Trimestre"}
            </span>
            {estimate?.start_date && estimate?.end_date && (
              <span className="text-[11px] text-text-secondary">
                Période : {formatDate(estimate.start_date)} au {formatDate(estimate.end_date)}
              </span>
            )}
          </div>
          {estimate && (
            <div className="flex items-center gap-1.5 text-xs text-status-success font-medium">
              <ShieldCheck className="w-4 h-4" />
              <span>Confiance : {estimate.confidence_index} %</span>
            </div>
          )}
        </div>

        {/* Montant Central & Fourchette */}
        {isEstimateLoading ? (
          <div className="space-y-2 py-2">
            <Skeleton className="h-10 w-48" />
            <Skeleton className="h-4 w-32" />
          </div>
        ) : (
          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl sm:text-4xl font-extrabold text-text-primary tabular-nums tracking-tight">
                {formatCurrency(estimate?.totals?.net_ttc_central)}
              </span>
              <span className="text-xs text-text-secondary font-medium">
                TTC (Net à payer)
              </span>
            </div>

            {/* Fourchette Bas / Haut */}
            <div className="flex items-center justify-between text-xs text-text-secondary mt-1.5">
              <span>Bas : {formatCurrency(estimate?.totals?.net_ttc_low)}</span>
              <span>Haut : {formatCurrency(estimate?.totals?.net_ttc_high)}</span>
            </div>
          </div>
        )}

        {/* Barre de progression du cycle trimestriel */}
        {estimate && (
          <div className="space-y-1.5 pt-1">
            <div className="flex justify-between text-xs text-text-secondary font-medium">
              <span>
                Avancement : {estimate.days_elapsed} / {estimate.total_days} jours
              </span>
              <span>{estimate.progress_pct} %</span>
            </div>
            <div className="w-full h-2 rounded-full bg-surface-elevated overflow-hidden border border-border/40">
              <div
                className="h-full bg-gradient-to-r from-[#38BDF8] to-[#34D399] rounded-full transition-all duration-300"
                style={{ width: `${Math.min(100, Number(estimate.progress_pct))}%` }}
              />
            </div>
          </div>
        )}

        {/* Comparaison au budget trimestriel */}
        {estimate && (
          <div className="pt-2 border-t border-border/50 flex items-center justify-between text-xs">
            <span className="text-text-secondary">
              Budget cible : {formatCurrency(estimate.totals.budget_target)}
            </span>
            <span
              className={
                estimate.totals.target_variance > 0
                  ? "text-status-danger font-semibold flex items-center gap-0.5"
                  : "text-status-success font-semibold flex items-center gap-0.5"
              }
            >
              {estimate.totals.target_variance > 0 ? (
                <>
                  <TrendingUp className="w-3.5 h-3.5" /> +
                  {formatCurrency(estimate.totals.target_variance)}
                </>
              ) : (
                <>
                  <TrendingDown className="w-3.5 h-3.5" />
                  {formatCurrency(estimate.totals.target_variance)}
                </>
              )}
            </span>
          </div>
        )}
      </Card>

      {/* TROIS CARTES ÉNERGIE */}
      <div className="grid grid-cols-1 gap-3">
        {/* 1. ÉLECTRICITÉ (Jaune #FACC15) */}
        <Card className="p-4 space-y-3 border-l-4 border-l-[#FACC15]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-[#FACC15]/15 text-[#FACC15]">
                <Zap className="w-4 h-4" />
              </span>
              <span className="font-bold text-sm text-text-primary">Électricité</span>
            </div>
            {sparklines?.electricity?.variation_pct !== undefined && (
              <Badge
                status={sparklines.electricity.variation_pct <= 0 ? "success" : "warning"}
                icon={false}
              >
                {formatPercent(sparklines.electricity.variation_pct)} vs N-1
              </Badge>
            )}
          </div>

          <div className="flex items-end justify-between">
            <div>
              <p className="text-2xl font-extrabold text-text-primary tabular-nums">
                {formatConsumption(estimate?.sonelgaz?.electricity_projected, "kWh")}
              </p>
              <p className="text-xs text-text-secondary mt-0.5">
                Réel : +{formatConsumption(estimate?.sonelgaz?.electricity_realized, "kWh")}
                {estimate?.sonelgaz?.baseline_index_elec && (
                  <span className="block text-[10px] opacity-75">
                    Depuis repère facture ({estimate.sonelgaz.baseline_index_elec} kWh)
                  </span>
                )}
              </p>
            </div>
            <div className="w-32 h-12">
              <SparklineArea
                data={sparklines?.electricity?.values || [12, 14, 18, 15, 16, 20, 19]}
                color="#FACC15"
                height={48}
              />
            </div>
          </div>
        </Card>

        {/* 2. GAZ NATUREL (Orange #FF7A45) */}
        <Card className="p-4 space-y-3 border-l-4 border-l-[#FF7A45]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-[#FF7A45]/15 text-[#FF7A45]">
                <Flame className="w-4 h-4" />
              </span>
              <span className="font-bold text-sm text-text-primary">Gaz Naturel</span>
            </div>
            {sparklines?.gas?.variation_pct !== undefined && (
              <Badge
                status={sparklines.gas.variation_pct <= 0 ? "success" : "warning"}
                icon={false}
              >
                {formatPercent(sparklines.gas.variation_pct)} vs N-1
              </Badge>
            )}
          </div>

          <div className="flex items-end justify-between">
            <div>
              <p className="text-2xl font-extrabold text-text-primary tabular-nums">
                {formatConsumption(estimate?.sonelgaz?.gas_projected_m3, "m³")}
              </p>
              <p className="text-xs text-text-secondary mt-0.5">
                Réel : +{formatConsumption(estimate?.sonelgaz?.gas_realized_m3, "m³")} (
                {formatConsumption(
                  Number(estimate?.sonelgaz?.gas_realized_m3 || 0) * 9.7,
                  "Th"
                )}
                )
                {estimate?.sonelgaz?.baseline_index_gas && (
                  <span className="block text-[10px] opacity-75">
                    Depuis repère facture ({estimate.sonelgaz.baseline_index_gas} m³)
                  </span>
                )}
              </p>
            </div>
            <div className="w-32 h-12">
              <SparklineArea
                data={sparklines?.gas?.values || [8, 10, 15, 12, 14, 16, 15]}
                color="#FF7A45"
                height={48}
              />
            </div>
          </div>
        </Card>

        {/* 3. EAU (Bleu #38BDF8) */}
        <Card className="p-4 space-y-3 border-l-4 border-l-[#38BDF8]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-[#38BDF8]/15 text-[#38BDF8]">
                <Droplets className="w-4 h-4" />
              </span>
              <span className="font-bold text-sm text-text-primary">Eau & Assainissement</span>
            </div>
            {sparklines?.water?.variation_pct !== undefined && (
              <Badge
                status={sparklines.water.variation_pct <= 0 ? "success" : "warning"}
                icon={false}
              >
                {formatPercent(sparklines.water.variation_pct)} vs N-1
              </Badge>
            )}
          </div>

          <div className="flex items-end justify-between">
            <div>
              <p className="text-2xl font-extrabold text-text-primary tabular-nums">
                {formatConsumption(estimate?.water?.water_projected_m3, "m³")}
              </p>
              <p className="text-xs text-text-secondary mt-0.5">
                Réel : {formatConsumption(estimate?.water?.water_realized_m3, "m³")}
              </p>
            </div>
            <div className="w-32 h-12">
              <SparklineArea
                data={sparklines?.water?.values || [2, 3, 2, 4, 3, 3, 2]}
                color="#38BDF8"
                height={48}
              />
            </div>
          </div>
        </Card>
      </div>

      {/* DERNIERS RELEVÉS AVEC ACTIONS MODIFIER & SUPPRIMER */}
      <div className="space-y-2 pt-2">
        <div className="flex items-center justify-between px-1">
          <h3 className="text-xs font-bold uppercase tracking-wider text-text-secondary">
            Derniers relevés enregistrés
          </h3>
          <span
            className="text-xs text-[#38BDF8] font-medium cursor-pointer tap-target-44 flex items-center"
            onClick={() => setIsSaisieOpen(true)}
          >
            + Nouveau
          </span>
        </div>

        {isReadingsLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </div>
        ) : readings && readings.length > 0 ? (
          <div className="space-y-2">
            {readings.map((r) => {
              const icon =
                r.meter_type === "electricity" ? (
                  <Zap className="w-4 h-4 text-[#FACC15]" />
                ) : r.meter_type === "gas" ? (
                  <Flame className="w-4 h-4 text-[#FF7A45]" />
                ) : (
                  <Droplets className="w-4 h-4 text-[#38BDF8]" />
                );

              const unit = r.meter_type === "electricity" ? "kWh" : "m³";

              return (
                <div
                  key={r.id}
                  className="p-3 rounded-xl bg-surface border border-border flex items-center justify-between tap-target-44 gap-2"
                >
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <span className="p-2 rounded-lg bg-surface-elevated flex-shrink-0">
                      {icon}
                    </span>
                    <div className="min-w-0">
                      <p className="text-sm font-bold text-text-primary tabular-nums truncate">
                        {formatConsumption(r.index_value, unit)}
                      </p>
                      <p className="text-xs text-text-secondary truncate">
                        {formatDate(r.read_at)} {r.note && `• ${r.note}`}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 flex-shrink-0">
                    {r.consumption_since_previous !== null && (
                      <div className="text-right hidden xs:block">
                        <span className="text-xs font-semibold text-text-primary tabular-nums block">
                          +{formatConsumption(r.consumption_since_previous, unit)}
                        </span>
                        {r.daily_rate !== null && (
                          <span className="text-[10px] text-text-secondary block">
                            {formatNumber(r.daily_rate, 1)}/j
                          </span>
                        )}
                      </div>
                    )}

                    {/* Boutons Modifier & Supprimer */}
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => handleOpenEdit(r)}
                        className="p-2 rounded-lg bg-surface-elevated text-text-secondary hover:text-[#38BDF8] active:scale-95 transition-all tap-target-44 flex items-center justify-center"
                        title="Modifier ce relevé"
                        aria-label="Modifier"
                      >
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => setDeletingReading(r)}
                        className="p-2 rounded-lg bg-surface-elevated text-text-secondary hover:text-status-danger active:scale-95 transition-all tap-target-44 flex items-center justify-center"
                        title="Supprimer ce relevé"
                        aria-label="Supprimer"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <Card className="text-center py-6 text-text-secondary text-sm">
            Aucun relevé enregistré. Cliquez sur « + » pour commencer.
          </Card>
        )}
      </div>

      {/* MODALE D'ÉDITION D'UN RELEVÉ */}
      <ModalSheet
        isOpen={!!editingReading}
        onClose={() => setEditingReading(null)}
        title="Modifier le relevé"
        subtitle={
          editingReading
            ? `${editingReading.meter_type === "electricity" ? "Électricité" : editingReading.meter_type === "gas" ? "Gaz" : "Eau"}`
            : undefined
        }
      >
        <div className="space-y-3">
          <div>
            <label className="text-xs font-semibold text-text-secondary">Date du relevé</label>
            <input
              type="date"
              value={editDate}
              onChange={(e) => setEditDate(e.target.value)}
              className="w-full bg-surface border border-border rounded-xl p-2.5 text-xs text-text-primary mt-1 tap-target-44"
              required
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-text-secondary">
              Nouvel index (
              {editingReading?.meter_type === "electricity" ? "kWh" : "m³"})
            </label>
            <input
              type="number"
              step="any"
              inputMode="decimal"
              value={editIndex}
              onChange={(e) => setEditIndex(e.target.value)}
              className="w-full bg-surface border border-border rounded-xl p-2.5 text-sm font-bold text-text-primary mt-1 tap-target-44"
              required
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-text-secondary">Note ou commentaire (optionnel)</label>
            <input
              type="text"
              value={editNote}
              onChange={(e) => setEditNote(e.target.value)}
              placeholder="Ex: Correction de saisie"
              className="w-full bg-surface border border-border rounded-xl p-2.5 text-xs text-text-primary mt-1 tap-target-44"
            />
          </div>
          <div className="flex gap-2 pt-2">
            <Button
              className="flex-1 font-bold text-xs tap-target-44"
              onClick={() => updateReadingMutation.mutate()}
              loading={updateReadingMutation.isPending}
              disabled={!editIndex || !editDate}
            >
              Enregistrer les modifications
            </Button>
            <Button
              variant="outline"
              className="text-xs tap-target-44"
              onClick={() => setEditingReading(null)}
            >
              Annuler
            </Button>
          </div>
        </div>
      </ModalSheet>

      {/* MODALE DE CONFIRMATION DE SUPPRESSION */}
      <ModalSheet
        isOpen={!!deletingReading}
        onClose={() => setDeletingReading(null)}
        title="Supprimer ce relevé ?"
        subtitle="Cette action recalculera automatiquement les consommations et projections."
      >
        <div className="space-y-4">
          <div className="p-3.5 rounded-xl bg-status-danger/10 border border-status-danger/30 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-status-danger flex-shrink-0" />
            <p className="text-xs text-text-primary">
              Voulez-vous vraiment supprimer le relevé du{" "}
              <strong>{deletingReading && formatDate(deletingReading.read_at)}</strong> (Index :{" "}
              <strong>
                {deletingReading &&
                  formatConsumption(
                    deletingReading.index_value,
                    deletingReading.meter_type === "electricity" ? "kWh" : "m³"
                  )}
              </strong>
              ) ?
            </p>
          </div>

          <div className="flex gap-2">
            <Button
              variant="danger"
              className="flex-1 font-bold text-xs tap-target-44"
              onClick={() => deletingReading && deleteReadingMutation.mutate(deletingReading.id)}
              loading={deleteReadingMutation.isPending}
            >
              Confirmer la suppression
            </Button>
            <Button
              variant="outline"
              className="text-xs tap-target-44"
              onClick={() => setDeletingReading(null)}
            >
              Annuler
            </Button>
          </div>
        </div>
      </ModalSheet>

      <SaisieModal isOpen={isSaisieOpen} onClose={() => setIsSaisieOpen(false)} />
    </div>
  );
};
