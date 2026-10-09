import clsx from "clsx";

export interface SegmentOption<T extends string> {
  value: T;
  label: string;
}

interface SegmentedControlProps<T extends string> {
  options: SegmentOption<T>[];
  value: T;
  onChange: (value: T) => void;
  className?: string;
}

export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  className,
}: SegmentedControlProps<T>) {
  return (
    <div
      className={clsx(
        "flex p-1 bg-surface-elevated rounded-xl border border-border/60 select-none",
        className
      )}
    >
      {options.map((opt) => {
        const isSelected = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={clsx(
              "flex-1 py-1.5 px-3 text-xs sm:text-sm font-medium rounded-lg transition-all duration-150 text-center tap-target-44 flex items-center justify-center",
              isSelected
                ? "bg-surface text-text-primary shadow-sm font-semibold border border-border/40"
                : "text-text-secondary hover:text-text-primary"
            )}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
