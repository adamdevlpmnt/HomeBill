import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ModalSheet } from "../ui/ModalSheet";
import { Button } from "../ui/Button";
import { useToast } from "../ui/Toast";
import { apiFetch } from "../../lib/api";
import { formatConsumption, formatCurrency, formatDate } from "../../lib/formatters";
import { Zap, Flame, Droplets, AlertTriangle } from "lucide-react";

interface Meter {
  id: number;
  meter_type: "electricity" | "gas" | "water";
  name: string;
  unit: string;
  last_reading_date: string | null;
  last_index_value: string | number | null;
}

interface SaisieModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SaisieModal: React.FC<SaisieModalProps> = ({ isOpen, onClose }) => {
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  // Date par défaut : aujourd'hui au format YYYY-MM-DD
  const [readAt, setReadAt] = useState(() => {
    return new Date().toISOString().split("T")[0];
  });

  const [indexElec, setIndexElec] = useState("");
  const [indexGas, setIndexGas] = useState("");
  const [indexWater, setIndexWater] = useState("");
  const [note, setNote] = useState("");

  // Récupérer les 3 compteurs
  const { data: meters } = useQuery<Meter[]>({
    queryKey: ["meters"],
    queryFn: () => apiFetch<Meter[]>("/api/meters"),
    enabled: isOpen,
  });

  const elecMeter = meters?.find((m) => m.meter_type === "electricity");
  const gasMeter = meters?.find((m) => m.meter_type === "gas");
  const waterMeter = meters?.find((m) => m.meter_type === "water");

  // Pré-remplir les index lors de l'ouverture
  useEffect(() => {
    if (isOpen) {
      setIndexElec("");
      setIndexGas("");
      setIndexWater("");
      setNote("");
    }
  }, [isOpen]);

  // Calcul instantané des deltas en direct pendant la frappe
  const calcDelta = (valStr: string, lastVal: string | number | null | undefined) => {
    if (!valStr || lastVal === null || lastVal === undefined) return null;
    const current = parseFloat(valStr);
    const last = typeof lastVal === "string" ? parseFloat(lastVal) : lastVal;
    if (isNaN(current) || isNaN(last)) return null;
    const diff = current - last;
    return diff;
  };

  const deltaElec = calcDelta(indexElec, elecMeter?.last_index_value);
  const deltaGas = calcDelta(indexGas, gasMeter?.last_index_value);
  const deltaWater = calcDelta(indexWater, waterMeter?.last_index_value);

  // Estimation approximative instantanée de coût
  const costElec = deltaElec && deltaElec > 0 ? deltaElec * 4.55 : 0;
  const costGas = deltaGas && deltaGas > 0 ? deltaGas * 9.7 * 0.35 : 0;
  const costWater = deltaWater && deltaWater > 0 ? deltaWater * 12.0 : 0;
  const totalCost = costElec + costGas + costWater;

  const saveMutation = useMutation({
    mutationFn: async () => {
      const readings = [];
      if (elecMeter && indexElec) {
        readings.push({ meter_id: elecMeter.id, index_value: parseFloat(indexElec) });
      }
      if (gasMeter && indexGas) {
        readings.push({ meter_id: gasMeter.id, index_value: parseFloat(indexGas) });
      }
      if (waterMeter && indexWater) {
        readings.push({ meter_id: waterMeter.id, index_value: parseFloat(indexWater) });
      }

      if (readings.length === 0) {
        throw new Error("Veuillez saisir au moins un index.");
      }

      return apiFetch("/api/readings/bulk", {
        method: "POST",
        body: JSON.stringify({
          read_at: readAt,
          readings,
          note: note.trim() || undefined,
        }),
      });
    },
    onSuccess: () => {
      showToast("Relevés enregistrés avec succès !");
      queryClient.invalidateQueries({ queryKey: ["meters"] });
      queryClient.invalidateQueries({ queryKey: ["readings"] });
      queryClient.invalidateQueries({ queryKey: ["billing_estimate"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
      queryClient.invalidateQueries({ queryKey: ["sparklines"] });
      onClose();
    },
    onError: (err: any) => {
      showToast(err.message || "Erreur lors de l'enregistrement", "error");
    },
  });

  return (
    <ModalSheet
      isOpen={isOpen}
      onClose={onClose}
      title="Nouveau relevé"
      subtitle="Saisie rapide des index des 3 compteurs"
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          saveMutation.mutate();
        }}
        className="space-y-4"
      >
        {/* Date du relevé */}
        <div>
          <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1">
            Date du relevé
          </label>
          <input
            type="date"
            value={readAt}
            onChange={(e) => setReadAt(e.target.value)}
            className="w-full bg-surface-elevated border border-border rounded-xl px-3.5 py-2.5 text-text-primary text-base font-medium focus:outline-none focus:border-[#38BDF8] tap-target-44"
            required
          />
        </div>

        {/* 1. Électricité */}
        <div className="p-3.5 rounded-2xl bg-surface-elevated/60 border border-border/80 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-[#FACC15]/15 text-[#FACC15]">
                <Zap className="w-4 h-4" />
              </span>
              <span className="font-semibold text-sm">Électricité</span>
            </div>
            {elecMeter && (
              <span className="text-xs text-text-secondary">
                Dernier : {formatConsumption(elecMeter.last_index_value, "kWh")}
                {elecMeter.last_reading_date && ` (${formatDate(elecMeter.last_reading_date)})`}
              </span>
            )}
          </div>
          <div className="relative">
            <input
              type="number"
              step="any"
              inputMode="decimal"
              placeholder={elecMeter?.last_index_value ? `Ex: ${elecMeter.last_index_value}` : "Nouvel index"}
              value={indexElec}
              onChange={(e) => setIndexElec(e.target.value)}
              className="w-full bg-surface border border-border rounded-xl px-3.5 py-2.5 text-text-primary text-base font-bold tabular-nums focus:outline-none focus:border-[#FACC15] tap-target-44"
            />
            <span className="absolute right-3.5 top-3 text-xs font-bold text-text-secondary">
              kWh
            </span>
          </div>
          {deltaElec !== null && (
            <div className="flex items-center justify-between text-xs pt-1 px-1">
              <span className={deltaElec < 0 ? "text-status-danger font-semibold flex items-center gap-1" : "text-text-secondary"}>
                {deltaElec < 0 && <AlertTriangle className="w-3.5 h-3.5" />}
                {deltaElec < 0 ? "Index inférieur au précédent !" : `+${formatConsumption(deltaElec, "kWh")}`}
              </span>
              {deltaElec > 0 && (
                <span className="text-text-secondary">~ {formatCurrency(costElec)}</span>
              )}
            </div>
          )}
        </div>

        {/* 2. Gaz */}
        <div className="p-3.5 rounded-2xl bg-surface-elevated/60 border border-border/80 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-[#FF7A45]/15 text-[#FF7A45]">
                <Flame className="w-4 h-4" />
              </span>
              <span className="font-semibold text-sm">Gaz Naturel</span>
            </div>
            {gasMeter && (
              <span className="text-xs text-text-secondary">
                Dernier : {formatConsumption(gasMeter.last_index_value, "m³")}
                {gasMeter.last_reading_date && ` (${formatDate(gasMeter.last_reading_date)})`}
              </span>
            )}
          </div>
          <div className="relative">
            <input
              type="number"
              step="any"
              inputMode="decimal"
              placeholder={gasMeter?.last_index_value ? `Ex: ${gasMeter.last_index_value}` : "Nouvel index"}
              value={indexGas}
              onChange={(e) => setIndexGas(e.target.value)}
              className="w-full bg-surface border border-border rounded-xl px-3.5 py-2.5 text-text-primary text-base font-bold tabular-nums focus:outline-none focus:border-[#FF7A45] tap-target-44"
            />
            <span className="absolute right-3.5 top-3 text-xs font-bold text-text-secondary">
              m³
            </span>
          </div>
          {deltaGas !== null && (
            <div className="flex items-center justify-between text-xs pt-1 px-1">
              <span className={deltaGas < 0 ? "text-status-danger font-semibold flex items-center gap-1" : "text-text-secondary"}>
                {deltaGas < 0 && <AlertTriangle className="w-3.5 h-3.5" />}
                {deltaGas < 0 ? "Index inférieur au précédent !" : `+${formatConsumption(deltaGas, "m³")} (${formatConsumption(deltaGas * 9.7, "Th")})`}
              </span>
              {deltaGas > 0 && (
                <span className="text-text-secondary">~ {formatCurrency(costGas)}</span>
              )}
            </div>
          )}
        </div>

        {/* 3. Eau */}
        <div className="p-3.5 rounded-2xl bg-surface-elevated/60 border border-border/80 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-[#38BDF8]/15 text-[#38BDF8]">
                <Droplets className="w-4 h-4" />
              </span>
              <span className="font-semibold text-sm">Eau</span>
            </div>
            {waterMeter && (
              <span className="text-xs text-text-secondary">
                Dernier : {formatConsumption(waterMeter.last_index_value, "m³")}
                {waterMeter.last_reading_date && ` (${formatDate(waterMeter.last_reading_date)})`}
              </span>
            )}
          </div>
          <div className="relative">
            <input
              type="number"
              step="any"
              inputMode="decimal"
              placeholder={waterMeter?.last_index_value ? `Ex: ${waterMeter.last_index_value}` : "Nouvel index"}
              value={indexWater}
              onChange={(e) => setIndexWater(e.target.value)}
              className="w-full bg-surface border border-border rounded-xl px-3.5 py-2.5 text-text-primary text-base font-bold tabular-nums focus:outline-none focus:border-[#38BDF8] tap-target-44"
            />
            <span className="absolute right-3.5 top-3 text-xs font-bold text-text-secondary">
              m³
            </span>
          </div>
          {deltaWater !== null && (
            <div className="flex items-center justify-between text-xs pt-1 px-1">
              <span className={deltaWater < 0 ? "text-status-danger font-semibold flex items-center gap-1" : "text-text-secondary"}>
                {deltaWater < 0 && <AlertTriangle className="w-3.5 h-3.5" />}
                {deltaWater < 0 ? "Index inférieur au précédent !" : `+${formatConsumption(deltaWater, "m³")}`}
              </span>
              {deltaWater > 0 && (
                <span className="text-text-secondary">~ {formatCurrency(costWater)}</span>
              )}
            </div>
          )}
        </div>

        {/* Note optionnelle */}
        <div>
          <input
            type="text"
            placeholder="Note ou commentaire (optionnel)"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            className="w-full bg-surface-elevated/40 border border-border rounded-xl px-3.5 py-2 text-text-primary text-sm focus:outline-none focus:border-[#38BDF8]"
          />
        </div>

        {/* Aperçu du coût total estimé de la semaine */}
        {totalCost > 0 && (
          <div className="flex items-center justify-between px-3 py-2 rounded-xl bg-surface border border-border">
            <span className="text-xs text-text-secondary">Coût estimé du relevé :</span>
            <span className="text-sm font-bold text-text-primary tabular-nums">
              ~ {formatCurrency(totalCost)}
            </span>
          </div>
        )}

        {/* Bouton de validation en 1 action */}
        <Button
          type="submit"
          className="w-full mt-2 font-bold"
          loading={saveMutation.isPending}
          disabled={!indexElec && !indexGas && !indexWater}
        >
          Valider les relevés
        </Button>
      </form>
    </ModalSheet>
  );
};
