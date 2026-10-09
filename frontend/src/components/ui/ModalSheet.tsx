import React, { useEffect } from "react";
import clsx from "clsx";
import { X } from "lucide-react";

interface ModalSheetProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  fullScreenMobile?: boolean;
}

export const ModalSheet: React.FC<ModalSheetProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  fullScreenMobile = true,
}) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-200"
        onClick={onClose}
      />

      {/* Sheet Content */}
      <div
        className={clsx(
          "relative w-full max-w-lg bg-surface border-t sm:border border-border rounded-t-3xl sm:rounded-2xl shadow-floating z-10 flex flex-col max-h-[92vh] sm:max-h-[85vh] transition-transform duration-200 animate-in slide-in-from-bottom",
          fullScreenMobile && "h-auto"
        )}
      >
        {/* Poignée iOS pour mobile */}
        <div className="flex justify-center pt-3 pb-1 sm:hidden">
          <div className="w-10 h-1 rounded-full bg-border" />
        </div>

        {/* En-tête */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-border/50">
          <div>
            {title && <h2 className="text-lg font-bold text-text-primary">{title}</h2>}
            {subtitle && <p className="text-xs text-text-secondary mt-0.5">{subtitle}</p>}
          </div>
          <button
            onClick={onClose}
            className="w-9 h-9 rounded-full flex items-center justify-center bg-surface-elevated text-text-secondary hover:text-text-primary border border-border/50 tap-target-44"
            aria-label="Fermer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Corps défilable */}
        <div className="p-5 overflow-y-auto flex-1 pb-safe-bottom">
          {children}
        </div>
      </div>
    </div>
  );
};
