import React from "react";
import clsx from "clsx";
import { Zap, Flame, Droplets } from "lucide-react";

export type EnergyFilterKey = "electricity" | "gas" | "water" | "all";

interface EnergyPillProps {
  energy: EnergyFilterKey;
  label?: string;
  active: boolean;
  onClick: () => void;
  className?: string;
}

export const EnergyPill: React.FC<EnergyPillProps> = ({
  energy,
  label,
  active,
  onClick,
  className,
}) => {
  let icon = null;
  let defaultLabel = "Tous";
  let activeBorderAndText = "border-text-primary text-text-primary";

  if (energy === "electricity") {
    icon = <Zap className="w-4 h-4 text-[#FACC15]" />;
    defaultLabel = "Électricité";
    activeBorderAndText = "border-[#FACC15] text-[#FACC15] bg-[#FACC15]/10";
  } else if (energy === "gas") {
    icon = <Flame className="w-4 h-4 text-[#FF7A45]" />;
    defaultLabel = "Gaz";
    activeBorderAndText = "border-[#FF7A45] text-[#FF7A45] bg-[#FF7A45]/10";
  } else if (energy === "water") {
    icon = <Droplets className="w-4 h-4 text-[#38BDF8]" />;
    defaultLabel = "Eau";
    activeBorderAndText = "border-[#38BDF8] text-[#38BDF8] bg-[#38BDF8]/10";
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        "inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs sm:text-sm font-medium border transition-all duration-150 tap-target-44 active:scale-95",
        active
          ? `${activeBorderAndText} shadow-sm font-semibold`
          : "border-border text-text-secondary bg-surface hover:text-text-primary hover:border-border/80",
        className
      )}
    >
      {icon}
      <span>{label || defaultLabel}</span>
    </button>
  );
};
