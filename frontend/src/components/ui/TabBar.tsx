import React from "react";
import { NavLink } from "react-router-dom";
import clsx from "clsx";
import { Home, BarChart3, Receipt, Settings, Plus } from "lucide-react";

interface TabBarProps {
  onOpenSaisie: () => void;
}

export const TabBar: React.FC<TabBarProps> = ({ onOpenSaisie }) => {
  const navItemClass = ({ isActive }: { isActive: boolean }) =>
    clsx(
      "flex flex-col items-center justify-center flex-1 h-full tap-target-44 transition-colors duration-150 relative py-1",
      isActive
        ? "text-[#38BDF8] font-semibold"
        : "text-text-secondary hover:text-text-primary"
    );

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-surface/95 dark:bg-[#131A2E]/95 backdrop-blur-xl border-t border-border shadow-soft pb-[env(safe-area-inset-bottom,16px)]">
      <div className="max-w-md mx-auto px-2 h-16 flex items-center justify-around relative">
        {/* Onglet 1 : Accueil */}
        <NavLink to="/" className={navItemClass} end>
          {({ isActive }) => (
            <>
              <Home className={clsx("w-5 h-5", isActive && "stroke-[2.5]")} />
              <span className="text-[10px] mt-1 font-medium">Accueil</span>
              {isActive && (
                <span className="absolute bottom-1 w-1 h-1 rounded-full bg-[#38BDF8]" />
              )}
            </>
          )}
        </NavLink>

        {/* Onglet 2 : Analyses */}
        <NavLink to="/analyses" className={navItemClass}>
          {({ isActive }) => (
            <>
              <BarChart3 className={clsx("w-5 h-5", isActive && "stroke-[2.5]")} />
              <span className="text-[10px] mt-1 font-medium">Analyses</span>
              {isActive && (
                <span className="absolute bottom-1 w-1 h-1 rounded-full bg-[#38BDF8]" />
              )}
            </>
          )}
        </NavLink>

        {/* Bouton Central : Saisie (+) */}
        <div className="flex items-center justify-center flex-1 -mt-6">
          <button
            type="button"
            onClick={onOpenSaisie}
            className="w-14 h-14 rounded-full bg-[#38BDF8] text-slate-950 shadow-lg flex items-center justify-center active:scale-95 transition-transform duration-150 border-4 border-background tap-target-44"
            aria-label="Nouveau relevé"
          >
            <Plus className="w-7 h-7 stroke-[2.5]" />
          </button>
        </div>

        {/* Onglet 3 : Facture */}
        <NavLink to="/facture" className={navItemClass}>
          {({ isActive }) => (
            <>
              <Receipt className={clsx("w-5 h-5", isActive && "stroke-[2.5]")} />
              <span className="text-[10px] mt-1 font-medium">Facture</span>
              {isActive && (
                <span className="absolute bottom-1 w-1 h-1 rounded-full bg-[#38BDF8]" />
              )}
            </>
          )}
        </NavLink>

        {/* Onglet 4 : Réglages */}
        <NavLink to="/reglages" className={navItemClass}>
          {({ isActive }) => (
            <>
              <Settings className={clsx("w-5 h-5", isActive && "stroke-[2.5]")} />
              <span className="text-[10px] mt-1 font-medium">Réglages</span>
              {isActive && (
                <span className="absolute bottom-1 w-1 h-1 rounded-full bg-[#38BDF8]" />
              )}
            </>
          )}
        </NavLink>
      </div>
    </div>
  );
};
