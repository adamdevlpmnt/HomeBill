import React from "react";
import clsx from "clsx";

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className, ...props }) => {
  return (
    <div
      className={clsx(
        "animate-pulse rounded-xl bg-surface-elevated/80 border border-border/30",
        className
      )}
      {...props}
    />
  );
};
