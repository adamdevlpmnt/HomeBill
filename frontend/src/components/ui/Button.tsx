import React from "react";
import clsx from "clsx";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  className,
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  ...props
}) => {
  const baseStyles =
    "inline-flex items-center justify-center font-medium rounded-xl transition-all duration-150 active:scale-[0.98] tap-target-44 disabled:opacity-50 disabled:pointer-events-none";

  const sizeStyles = {
    sm: "px-3 py-1.5 text-sm min-h-[40px]",
    md: "px-4 py-2 text-base min-h-[44px]",
    lg: "px-6 py-3 text-lg min-h-[50px]",
  };

  const variantStyles = {
    primary: "bg-[#38BDF8] text-slate-900 font-semibold shadow-soft hover:bg-[#38BDF8]/90",
    secondary: "bg-surface-elevated text-text-primary hover:bg-surface-elevated/80 border border-border",
    outline: "border border-border text-text-primary hover:bg-surface-elevated/50",
    ghost: "text-text-secondary hover:text-text-primary hover:bg-surface-elevated/30",
    danger: "bg-status-danger text-white hover:bg-status-danger/90",
  };

  return (
    <button
      className={clsx(baseStyles, sizeStyles[size], variantStyles[variant], className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
      ) : null}
      {children}
    </button>
  );
};
