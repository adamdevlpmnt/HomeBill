import React from "react";
import clsx from "clsx";
import { Zap, Flame, Droplets, CheckCircle2, AlertTriangle, AlertCircle } from "lucide-react";

export type EnergyType = "electricity" | "gas" | "water";
export type StatusType = "success" | "warning" | "danger" | "neutral";

interface BadgeProps {
  energy?: EnergyType;
  status?: StatusType;
  label?: string;
  icon?: boolean;
  className?: string;
  children?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  energy,
  status,
  label,
  icon = true,
  className,
  children,
}) => {
  let colorClass = "bg-surface-elevated text-text-primary border-border";
  let IconComponent = null;

  if (energy === "electricity") {
    colorClass = "bg-[#FACC15]/15 text-[#FACC15] dark:text-[#FACC15] border-[#FACC15]/30";
    IconComponent = Zap;
  } else if (energy === "gas") {
    colorClass = "bg-[#FF7A45]/15 text-[#FF7A45] dark:text-[#FF7A45] border-[#FF7A45]/30";
    IconComponent = Flame;
  } else if (energy === "water") {
    colorClass = "bg-[#38BDF8]/15 text-[#38BDF8] dark:text-[#38BDF8] border-[#38BDF8]/30";
    IconComponent = Droplets;
  } else if (status === "success") {
    colorClass = "bg-[#34D399]/15 text-[#34D399] border-[#34D399]/30";
    IconComponent = CheckCircle2;
  } else if (status === "warning") {
    colorClass = "bg-[#FBBF24]/15 text-[#FBBF24] border-[#FBBF24]/30";
    IconComponent = AlertTriangle;
  } else if (status === "danger") {
    colorClass = "bg-[#F87171]/15 text-[#F87171] border-[#F87171]/30";
    IconComponent = AlertCircle;
  }

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border",
        colorClass,
        className
      )}
    >
      {icon && IconComponent && <IconComponent className="w-3.5 h-3.5" />}
      {children || label}
    </span>
  );
};
