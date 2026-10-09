import React, { createContext, useContext, useState, useCallback } from "react";
import clsx from "clsx";
import { CheckCircle2, AlertCircle, Info, X } from "lucide-react";

type ToastType = "success" | "error" | "info";

interface ToastMessage {
  id: string;
  type: ToastType;
  message: string;
}

interface ToastContextType {
  showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = useCallback((message: string, type: ToastType = "success") => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, type, message }]);

    // Auto-suppression après 3.5 secondes
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {/* Toast container en haut pour iOS */}
      <div className="fixed top-safe-top pt-4 inset-x-0 z-50 pointer-events-none flex flex-col items-center gap-2 px-4">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={clsx(
              "pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-2xl shadow-floating text-sm font-medium border max-w-sm w-full animate-in fade-in slide-in-from-top-4 duration-200",
              t.type === "success" && "bg-surface border-status-success/40 text-status-success",
              t.type === "error" && "bg-surface border-status-danger/40 text-status-danger",
              t.type === "info" && "bg-surface border-[#38BDF8]/40 text-[#38BDF8]"
            )}
          >
            {t.type === "success" && <CheckCircle2 className="w-5 h-5 flex-shrink-0" />}
            {t.type === "error" && <AlertCircle className="w-5 h-5 flex-shrink-0" />}
            {t.type === "info" && <Info className="w-5 h-5 flex-shrink-0" />}
            <span className="flex-1 text-text-primary text-xs sm:text-sm font-medium">{t.message}</span>
            <button
              onClick={() => removeToast(t.id)}
              className="text-text-secondary hover:text-text-primary tap-target-44 p-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast doit être utilisé au sein de ToastProvider");
  }
  return context;
}
