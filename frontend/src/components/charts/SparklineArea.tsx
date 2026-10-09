import React from "react";
import { AreaChart, Area, ResponsiveContainer } from "recharts";

interface SparklineAreaProps {
  data: number[];
  color: string;
  height?: number;
}

export const SparklineArea: React.FC<SparklineAreaProps> = ({
  data,
  color,
  height = 48,
}) => {
  if (!data || data.length === 0) {
    return <div style={{ height }} className="w-full" />;
  }

  const chartData = data.map((val, idx) => ({ idx, val }));
  const gradientId = `grad-${color.replace("#", "")}`;

  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 2, right: 2, left: 2, bottom: 2 }}>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.4} />
              <stop offset="100%" stopColor={color} stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey="val"
            stroke={color}
            strokeWidth={2}
            fill={`url(#${gradientId})`}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
