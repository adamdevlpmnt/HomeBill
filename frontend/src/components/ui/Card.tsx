import React from "react";
import clsx from "clsx";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  elevated?: boolean;
  bordered?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  elevated = false,
  bordered = true,
  ...props
}) => {
  return (
    <div
      className={clsx(
        "rounded-2xl p-4 transition-all duration-200",
        elevated ? "bg-surface-elevated shadow-soft" : "bg-surface shadow-card",
        bordered && "border border-border",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
