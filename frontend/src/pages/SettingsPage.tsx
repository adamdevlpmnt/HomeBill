import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { ModalSheet } from "../components/ui/ModalSheet";
import { useTheme } from "../hooks/useTheme";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../components/ui/Toast";
import { apiFetch } from "../lib/api";
import { formatCurrency } from "../lib/formatters";
import {
  Sun,
  Moon,
  Smartphone,
  Download,
  Upload,
  RefreshCw,
  LogOut,
  Receipt,
  Zap,
  Flame,
  Droplets,
  Save,
} from "lucide-react";

export const SettingsPage: React.FC = () => {
  const { theme, setTheme } = useTheme();
  const { logout } = useAuth();
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  const [isEventModalOpen, setIsEventModalOpen] = useState(false);
  const [eventMeterId, setEventMeterId] = useState<number>(1);
  const [eventDate, setEventDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [eventOldIndex, setEventOldIndex] = useState("");
  const [eventNewIndex, setEventNewIndex] = useState("0");
  const [eventNote, setEventNote] = useState("");

  // Récupérer les settings
  const { data: settings } = useQuery<any>({
    queryKey: ["settings"],
    queryFn: () => apiFetch("/api/settings"),
  });

  const { data: meters } = useQuery<any[]>({
    queryKey: ["meters"],
    queryFn: () => apiFetch("/api/meters"),
  });

  // Budgets
  const [budgetSonelgaz, setBudgetSonelgaz] = useState("");
  const [budgetWater, setBudgetWater] = useState("");

  // Repères Sonelgaz
  const [lastDateSonelgaz, setLastDateSonelgaz] = useState("");
  const [lastIndexElec, setLastIndexElec] = useState("");
  const [lastIndexGas, setLastIndexGas] = useState("");
  const [nextReadSonelgaz, setNextReadSonelgaz] = useState("");
  const [nextCycleSonelgaz, setNextCycleSonelgaz] = useState("");

  // Repères Eau
  const [lastDateWater, setLastDateWater] = useState("");
  const [lastIndexWater, setLastIndexWater] = useState("");
  const [nextReadWater, setNextReadWater] = useState("");
  const [nextCycleWater, setNextCycleWater] = useState("");

  // Synchroniser l'état initial des formulaires avec les réglages du backend
  useEffect(() => {
    if (settings) {
      if (!budgetSonelgaz && settings.budget_sonelgaz_quarterly) {
        setBudgetSonelgaz(String(settings.budget_sonelgaz_quarterly));
      }
      if (!budgetWater && settings.budget_water_quarterly) {
        setBudgetWater(String(settings.budget_water_quarterly));
      }
      if (!lastDateSonelgaz && settings.last_invoice_date_sonelgaz) {
        setLastDateSonelgaz(settings.last_invoice_date_sonelgaz);
      }
      if (!lastIndexElec && settings.last_invoice_index_electricity !== undefined) {
        setLastIndexElec(String(settings.last_invoice_index_electricity));
      }
      if (!lastIndexGas && settings.last_invoice_index_gas !== undefined) {
        setLastIndexGas(String(settings.last_invoice_index_gas));
      }
      if (!nextReadSonelgaz && settings.next_read_date_sonelgaz) {
        setNextReadSonelgaz(settings.next_read_date_sonelgaz);
      }
      if (!nextCycleSonelgaz && settings.next_cycle_code_sonelgaz) {
        setNextCycleSonelgaz(settings.next_cycle_code_sonelgaz);
      }
      if (!lastDateWater && settings.last_invoice_date_water) {
        setLastDateWater(settings.last_invoice_date_water);
      }
      if (!lastIndexWater && settings.last_invoice_index_water !== undefined) {
        setLastIndexWater(String(settings.last_invoice_index_water));
      }
      if (!nextReadWater && settings.next_read_date_water) {
        setNextReadWater(settings.next_read_date_water);
      }
      if (!nextCycleWater && settings.next_cycle_code_water) {
        setNextCycleWater(settings.next_cycle_code_water);
      }
    }
  }, [settings]);

  // Mettre à jour les budgets
  const saveBudgetMutation = useMutation({
    mutationFn: () =>
      apiFetch("/api/settings", {
        method: "PUT",
        body: JSON.stringify({
          ...settings,
          budget_sonelgaz_quarterly: parseFloat(budgetSonelgaz || settings?.budget_sonelgaz_quarterly),
          budget_water_quarterly: parseFloat(budgetWater || settings?.budget_water_quarterly),
        }),
      }),
    onSuccess: () => {
      showToast("Budgets cibles enregistrés !");
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      queryClient.invalidateQueries({ queryKey: ["billing_estimate"] });
    },
    onError: (err: any) => {
      showToast(err.message || "Erreur lors de l'enregistrement", "error");
    },
  });

  // Mettre à jour les repères de facturation
  const saveAnchorsMutation = useMutation({
    mutationFn: () =>
      apiFetch("/api/settings", {
        method: "PUT",
        body: JSON.stringify({
          ...settings,
          last_invoice_date_sonelgaz: lastDateSonelgaz || settings?.last_invoice_date_sonelgaz,
          last_invoice_index_electricity: parseFloat(lastIndexElec || settings?.last_invoice_index_electricity),
          last_invoice_index_gas: parseFloat(lastIndexGas || settings?.last_invoice_index_gas),
          next_read_date_sonelgaz: nextReadSonelgaz || settings?.next_read_date_sonelgaz,
          next_cycle_code_sonelgaz: nextCycleSonelgaz || settings?.next_cycle_code_sonelgaz,
          last_invoice_date_water: lastDateWater || settings?.last_invoice_date_water,
          last_invoice_index_water: parseFloat(lastIndexWater || settings?.last_invoice_index_water),
          next_read_date_water: nextReadWater || settings?.next_read_date_water,
          next_cycle_code_water: nextCycleWater || settings?.next_cycle_code_water,
        }),
      }),
    onSuccess: () => {
      showToast("Repères de la dernière facture enregistrés !");
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      queryClient.invalidateQueries({ queryKey: ["billing_estimate"] });
    },
    onError: (err: any) => {
      showToast(err.message || "Erreur lors de l'enregistrement", "error");
    },
  });

  // Déclaration événement compteur (remplacement)
  const createEventMutation = useMutation({
    mutationFn: () =>
      apiFetch("/api/events", {
        method: "POST",
        body: JSON.stringify({
          meter_id: eventMeterId,
          event_type: "replacement",
          event_date: eventDate,
          old_index_end: parseFloat(eventOldIndex),
          new_index_start: parseFloat(eventNewIndex),
          note: eventNote || undefined,
        }),
      }),
    onSuccess: () => {
      showToast("Remplacement de compteur enregistré !");
      setIsEventModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ["readings"] });
      queryClient.invalidateQueries({ queryKey: ["meters"] });
      queryClient.invalidateQueries({ queryKey: ["billing_estimate"] });
    },
    onError: (err: any) => {
      showToast(err.message || "Erreur lors de l'enregistrement", "error");
    },
  });

  const handleExportJson = () => {
    window.location.href = "/api/settings/export/json";
  };

  const handleExportCsv = () => {
    window.location.href = "/api/settings/export/csv";
  };

  const handleImportJson = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      await apiFetch("/api/settings/import/json", {
        method: "POST",
        body: formData,
      });
      showToast("Données importées avec succès !");
      queryClient.invalidateQueries();
    } catch (err: any) {
      showToast(err.message || "Erreur lors de l'import", "error");
    }
  };

  return (
    <div className="space-y-4 pb-6">
      <h1 className="text-xl font-extrabold text-text-primary tracking-tight">
        Réglages
      </h1>

      {/* 1. APPARENCE & THÈME */}
      <Card className="p-4 space-y-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-text-secondary">
          Apparence & Thème
        </h2>
        <div className="grid grid-cols-3 gap-2">
          <button
            type="button"
            onClick={() => setTheme("dark")}
            className={`p-3 rounded-xl border flex flex-col items-center gap-1.5 transition-all tap-target-44 ${theme === "dark" ? "border-[#38BDF8] bg-[#38BDF8]/10 text-text-primary font-bold shadow-sm" : "border-border text-text-secondary bg-surface"}`}
          >
            <Moon className="w-5 h-5 text-indigo-400" />
            <span className="text-xs">Nuit</span>
          </button>
          <button
            type="button"
            onClick={() => setTheme("light")}
            className={`p-3 rounded-xl border flex flex-col items-center gap-1.5 transition-all tap-target-44 ${theme === "light" ? "border-[#38BDF8] bg-[#38BDF8]/10 text-text-primary font-bold shadow-sm" : "border-border text-text-secondary bg-surface"}`}
          >
            <Sun className="w-5 h-5 text-amber-500" />
            <span className="text-xs">Clair</span>
          </button>
          <button
            type="button"
            onClick={() => setTheme("auto")}
            className={`p-3 rounded-xl border flex flex-col items-center gap-1.5 transition-all tap-target-44 ${theme === "auto" ? "border-[#38BDF8] bg-[#38BDF8]/10 text-text-primary font-bold shadow-sm" : "border-border text-text-secondary bg-surface"}`}
          >
            <Smartphone className="w-5 h-5 text-[#38BDF8]" />
            <span className="text-xs">iOS Auto</span>
          </button>
        </div>
      </Card>

      {/* 2. REPÈRES DE LA DERNIÈRE FACTURE REÇUE (DELTA POUR LA PROCHAINE FACTURE) */}
      <Card elevated className="p-4 space-y-4 border-l-4 border-l-[#38BDF8]">
        <div className="flex items-center gap-2">
          <Receipt className="w-5 h-5 text-[#38BDF8]" />
          <div>
            <h2 className="text-sm font-bold text-text-primary">
              Repères de la dernière facture reçue
            </h2>
            <p className="text-[11px] text-text-secondary">
              Sert de point de départ (date & index) pour calculer le delta exact de la prochaine facture.
            </p>
          </div>
        </div>

        {/* SECTION SONELGAZ (ÉLEC + GAZ) */}
        <div className="p-3 rounded-xl bg-surface-elevated/40 border border-border/50 space-y-3">
          <div className="flex items-center gap-1.5 text-xs font-bold text-text-primary">
            <Zap className="w-3.5 h-3.5 text-[#FACC15]" />
            <Flame className="w-3.5 h-3.5 text-[#FF7A45]" />
            <span>Sonelgaz (Électricité & Gaz)</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] text-text-secondary font-medium">
                Date de fin dernière facture
              </label>
              <input
                type="date"
                value={lastDateSonelgaz}
                onChange={(e) => setLastDateSonelgaz(e.target.value)}
                className="w-full bg-surface border border-border rounded-xl px-2.5 py-1.5 text-xs text-text-primary mt-1 tap-target-44"
              />
            </div>
            <div>
              <label className="text-[11px] text-text-secondary font-medium">
                Date prochaine facture estimée
              </label>
              <input
                type="date"
                value={nextReadSonelgaz}
                onChange={(e) => setNextReadSonelgaz(e.target.value)}
                className="w-full bg-surface border border-border rounded-xl px-2.5 py-1.5 text-xs text-text-primary mt-1 tap-target-44"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-[11px] text-text-secondary font-medium">
                Dernier index Élec (kWh)
              </label>
              <input
                type="number"
                step="any"
                value={lastIndexElec}
                onChange={(e) => setLastIndexElec(e.target.value)}
                placeholder="7331"
                className="w-full bg-surface border border-border rounded-xl px-2.5 py-1.5 text-xs font-bold text-text-primary mt-1 tap-target-44"
              />
            </div>
            <div>
              <label className="text-[11px] text-text-secondary font-medium">
                Dernier index Gaz (m³)
              </label>
              <input
                type="number"
                step="any"
                value={lastIndexGas}
                onChange={(e) => setLastIndexGas(e.target.value)}
                placeholder="5611"
                className="w-full bg-surface border border-border rounded-xl px-2.5 py-1.5 text-xs font-bold text-text-primary mt-1 tap-target-44"
              />
            </div>
            <div>
              <label className="text-[11px] text-text-secondary font-medium">
                Trimestre cible
              </label>
              <input
                type="text"
                value={nextCycleSonelgaz}
                onChange={(e) => setNextCycleSonelgaz(e.target.value)}
                placeholder="2026-Q3"
                className="w-full bg-surface border border-border rounded-xl px-2.5 py-1.5 text-xs font-bold text-text-primary mt-1 tap-target-44"
              />
            </div>
          </div>
        </div>

        {/* SECTION SEAAL (EAU) */}
        <div className="p-3 rounded-xl bg-surface-elevated/40 border border-border/50 space-y-3">
          <div className="flex items-center gap-1.5 text-xs font-bold text-text-primary">
            <Droplets className="w-3.5 h-3.5 text-[#38BDF8]" />
            <span>SEAAL (Eau & Assainissement)</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] text-text-secondary font-medium">
                Date de fin dernière facture
              </label>
              <input
                type="date"
                value={lastDateWater}
                onChange={(e) => setLastDateWater(e.target.value)}
                className="w-full bg-surface border border-border rounded-xl px-2.5 py-1.5 text-xs text-text-primary mt-1 tap-target-44"
              />
            </div>
            <div>
              <label className="text-[11px] text-text-secondary font-medium">
                Date prochaine facture estimée
              </label>
              <input
                type="date"
                value={nextReadWater}
                onChange={(e) => setNextReadWater(e.target.value)}
                className="w-full bg-surface border border-border rounded-xl px-2.5 py-1.5 text-xs text-text-primary mt-1 tap-target-44"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] text-text-secondary font-medium">
                Dernier index Eau (m³)
              </label>
              <input
                type="number"
                step="any"
                value={lastIndexWater}
                onChange={(e) => setLastIndexWater(e.target.value)}
                placeholder="120"
                className="w-full bg-surface border border-border rounded-xl px-2.5 py-1.5 text-xs font-bold text-text-primary mt-1 tap-target-44"
              />
            </div>
            <div>
              <label className="text-[11px] text-text-secondary font-medium">
                Trimestre cible
              </label>
              <input
                type="text"
                value={nextCycleWater}
                onChange={(e) => setNextCycleWater(e.target.value)}
                placeholder="2025-Q3"
                className="w-full bg-surface border border-border rounded-xl px-2.5 py-1.5 text-xs font-bold text-text-primary mt-1 tap-target-44"
              />
            </div>
          </div>
        </div>

        <Button
          size="sm"
          onClick={() => saveAnchorsMutation.mutate()}
          loading={saveAnchorsMutation.isPending}
          className="w-full text-xs font-bold flex items-center justify-center gap-1.5 tap-target-44"
        >
          <Save className="w-3.5 h-3.5" /> Enregistrer les repères de facture
        </Button>
      </Card>

      {/* 3. BUDGETS CIBLES TRIMESTRIELS */}
      <Card className="p-4 space-y-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-text-secondary">
          Budgets cibles trimestriels
        </h2>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-text-secondary flex justify-between">
              <span>Budget Sonelgaz (Élec + Gaz)</span>
              <span className="font-bold text-text-primary">
                Actuel : {formatCurrency(settings?.budget_sonelgaz_quarterly)}
              </span>
            </label>
            <input
              type="number"
              placeholder="Ex: 7000"
              value={budgetSonelgaz}
              onChange={(e) => setBudgetSonelgaz(e.target.value)}
              className="w-full bg-surface-elevated border border-border rounded-xl px-3 py-2 text-sm text-text-primary font-bold mt-1 tap-target-44"
            />
          </div>
          <div>
            <label className="text-xs text-text-secondary flex justify-between">
              <span>Budget SEAAL (Eau & Assainissement)</span>
              <span className="font-bold text-text-primary">
                Actuel : {formatCurrency(settings?.budget_water_quarterly)}
              </span>
            </label>
            <input
              type="number"
              placeholder="Ex: 600"
              value={budgetWater}
              onChange={(e) => setBudgetWater(e.target.value)}
              className="w-full bg-surface-elevated border border-border rounded-xl px-3 py-2 text-sm text-text-primary font-bold mt-1 tap-target-44"
            />
          </div>
          <Button
            size="sm"
            onClick={() => saveBudgetMutation.mutate()}
            loading={saveBudgetMutation.isPending}
            disabled={!budgetSonelgaz && !budgetWater}
            className="w-full text-xs font-bold"
          >
            Mettre à jour les budgets
          </Button>
        </div>
      </Card>

      {/* 4. GESTION DES COMPTEURS & ÉVÉNEMENTS */}
      <Card className="p-4 space-y-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-text-secondary">
          Compteurs & Événements
        </h2>
        <p className="text-xs text-text-secondary">
          En cas de changement ou de réinitialisation de compteur par Sonelgaz ou la SEAAL.
        </p>
        <Button
          variant="secondary"
          className="w-full text-xs font-bold flex items-center gap-2 tap-target-44"
          onClick={() => setIsEventModalOpen(true)}
        >
          <RefreshCw className="w-4 h-4 text-[#38BDF8]" />
          Déclarer un remplacement de compteur
        </Button>
      </Card>

      {/* 5. SAUVEGARDE & EXPORT */}
      <Card className="p-4 space-y-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-text-secondary">
          Données & Sauvegarde
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          <Button
            variant="outline"
            className="text-xs flex items-center justify-center gap-1.5 tap-target-44"
            onClick={handleExportJson}
          >
            <Download className="w-4 h-4 text-[#38BDF8]" /> Exporter JSON
          </Button>
          <Button
            variant="outline"
            className="text-xs flex items-center justify-center gap-1.5 tap-target-44"
            onClick={handleExportCsv}
          >
            <Download className="w-4 h-4 text-[#FACC15]" /> Exporter CSV
          </Button>
          <label className="inline-flex items-center justify-center font-medium rounded-xl border border-border text-text-primary hover:bg-surface-elevated/50 text-xs px-3 py-2 cursor-pointer tap-target-44">
            <Upload className="w-4 h-4 text-[#34D399] mr-1.5" />
            <span>Importer JSON</span>
            <input
              type="file"
              accept=".json"
              onChange={handleImportJson}
              className="hidden"
            />
          </label>
        </div>
      </Card>

      {/* 6. DÉCONNEXION */}
      <div className="pt-2">
        <Button
          variant="ghost"
          className="w-full text-status-danger text-sm font-semibold flex items-center gap-2 tap-target-44"
          onClick={() => logout()}
        >
          <LogOut className="w-4 h-4" /> Se déconnecter
        </Button>
      </div>

      {/* MODALE DE DÉCLARATION DE REMPLACEMENT DE COMPTEUR */}
      <ModalSheet
        isOpen={isEventModalOpen}
        onClose={() => setIsEventModalOpen(false)}
        title="Remplacement de compteur"
        subtitle="Préserve le calcul exact sans fausser la différence d'index"
      >
        <div className="space-y-3">
          <div>
            <label className="text-xs text-text-secondary font-medium">Compteur concerné</label>
            <select
              value={eventMeterId}
              onChange={(e) => setEventMeterId(parseInt(e.target.value))}
              className="w-full bg-surface border border-border rounded-xl p-2.5 text-xs text-text-primary mt-1 tap-target-44"
            >
              {meters?.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.meter_type})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-text-secondary font-medium">Date de l'intervention</label>
            <input
              type="date"
              value={eventDate}
              onChange={(e) => setEventDate(e.target.value)}
              className="w-full bg-surface border border-border rounded-xl p-2.5 text-xs text-text-primary mt-1 tap-target-44"
            />
          </div>
          <div>
            <label className="text-xs text-text-secondary font-medium">Dernier index de l'ancien compteur</label>
            <input
              type="number"
              step="any"
              placeholder="Ex: 7331"
              value={eventOldIndex}
              onChange={(e) => setEventOldIndex(e.target.value)}
              className="w-full bg-surface border border-border rounded-xl p-2.5 text-xs font-bold text-text-primary mt-1 tap-target-44"
              required
            />
          </div>
          <div>
            <label className="text-xs text-text-secondary font-medium">Nouvel index de départ du nouveau compteur</label>
            <input
              type="number"
              step="any"
              placeholder="Ex: 0"
              value={eventNewIndex}
              onChange={(e) => setEventNewIndex(e.target.value)}
              className="w-full bg-surface border border-border rounded-xl p-2.5 text-xs font-bold text-text-primary mt-1 tap-target-44"
              required
            />
          </div>
          <div>
            <label className="text-xs text-text-secondary font-medium">Note ou commentaire</label>
            <input
              type="text"
              placeholder="Ex: Remplacement compteur défectueux"
              value={eventNote}
              onChange={(e) => setEventNote(e.target.value)}
              className="w-full bg-surface border border-border rounded-xl p-2.5 text-xs text-text-primary mt-1 tap-target-44"
            />
          </div>
          <Button
            size="lg"
            className="w-full text-xs font-bold mt-2"
            onClick={() => createEventMutation.mutate()}
            loading={createEventMutation.isPending}
            disabled={!eventOldIndex}
          >
            Confirmer le remplacement
          </Button>
        </div>
      </ModalSheet>
    </div>
  );
};
