import React, { useState } from "react";
import { Outlet, Navigate, useLocation } from "react-router-dom";
import { TabBar } from "../ui/TabBar";
import { useAuth } from "../../hooks/useAuth";
import { SaisieModal } from "../saisie/SaisieModal";

export const AppLayout: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [isSaisieOpen, setIsSaisieOpen] = useState(false);
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-[100dvh] bg-background flex flex-col items-center justify-center p-4">
        <div className="w-10 h-10 border-4 border-[#38BDF8] border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-text-secondary text-sm font-medium">Chargement de Conso Maison...</p>
      </div>
    );
  }

  if (!isAuthenticated && location.pathname !== "/login") {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-[100dvh] bg-background text-text-primary flex flex-col max-w-md mx-auto relative selection:bg-[#38BDF8]/20">
      {/* Contenu principal scrollable avec padding bas suffisant pour la barre de menu */}
      <main className="flex-1 px-4 pt-safe-top pt-4 pb-[calc(88px+env(safe-area-inset-bottom,16px))]">
        <Outlet />
      </main>

      {/* Barre d'onglets iOS ancrée en bas */}
      <TabBar onOpenSaisie={() => setIsSaisieOpen(true)} />

      {/* Feuille modale globale de saisie rapide */}
      <SaisieModal isOpen={isSaisieOpen} onClose={() => setIsSaisieOpen(false)} />
    </div>
  );
};
