import React, { useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Button } from "../components/ui/Button";
import { useToast } from "../components/ui/Toast";
import { Lock, Zap, Flame, Droplets } from "lucide-react";

export const Login: React.FC = () => {
  const [password, setPassword] = useState("");
  const { login, isLoggingIn, isAuthenticated } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  // Si déjà authentifié, redirection immédiate vers l'accueil
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password) return;
    try {
      await login(password);
      showToast("Connexion réussie !");
      navigate("/", { replace: true });
    } catch (err: any) {
      showToast(err.message || "Mot de passe incorrect", "error");
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center items-center px-4 max-w-sm mx-auto">
      <div className="w-full text-center space-y-6">
        {/* Logo / Icônes des 3 énergies */}
        <div className="flex items-center justify-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-[#FACC15]/15 border border-[#FACC15]/30 flex items-center justify-center text-[#FACC15] shadow-card">
            <Zap className="w-6 h-6" />
          </div>
          <div className="w-12 h-12 rounded-2xl bg-[#FF7A45]/15 border border-[#FF7A45]/30 flex items-center justify-center text-[#FF7A45] shadow-card">
            <Flame className="w-6 h-6" />
          </div>
          <div className="w-12 h-12 rounded-2xl bg-[#38BDF8]/15 border border-[#38BDF8]/30 flex items-center justify-center text-[#38BDF8] shadow-card">
            <Droplets className="w-6 h-6" />
          </div>
        </div>

        <div>
          <h1 className="text-2xl font-extrabold text-text-primary tracking-tight">
            Conso Maison
          </h1>
          <p className="text-text-secondary text-sm mt-1">
            Suivi et estimation de vos factures d'énergie
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 pt-4">
          <div className="relative">
            <input
              type="password"
              placeholder="Mot de passe d'accès"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-surface-elevated border border-border rounded-xl px-4 py-3 text-text-primary placeholder:text-text-secondary text-base focus:outline-none focus:border-[#38BDF8] tap-target-44"
              autoFocus
              required
            />
            <Lock className="w-4 h-4 text-text-secondary absolute right-3.5 top-3.5 pointer-events-none" />
          </div>

          <Button
            type="submit"
            className="w-full font-bold shadow-soft"
            loading={isLoggingIn}
          >
            Se connecter
          </Button>
        </form>

        <p className="text-xs text-text-secondary/70 pt-4">
          Session sécurisée pour votre foyer
        </p>
      </div>
    </div>
  );
};
