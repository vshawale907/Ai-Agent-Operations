/* ============================================================================
   ChartRenderer Component — High-performance Recharts visualization with dark theme
   ============================================================================ */

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import type { ChartData } from '../types';

interface ChartRendererProps {
  chartData: ChartData;
  height?: number;
}

const PALETTE = [
  '#00E5FF', // Primary Cyan
  '#A855F7', // Violet
  '#38BDF8', // Blue
  '#10B981', // Green
  '#F59E0B', // Amber
  '#EC4899', // Pink
  '#6366F1', // Indigo
];

const CATEGORY_COLORS: Record<string, string> = {
  'Software': '#38BDF8',
  'Platform': '#A855F7',
  'Security': '#10B981',
  'Automation': '#F59E0B',
  'Office Supplies': '#EC4899',
  'Networking': '#00E5FF',
  'Electronics': '#6366F1',
  'Services': '#14B8A6'
};

export const ChartRenderer = ({ chartData, height = 320 }: ChartRendererProps) => {
  const { chart_type, title, data, x_key, y_key, keys } = chartData;

  if (!data || data.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-slate-500 text-sm border border-dashed border-white/10 rounded-xl"
        style={{ height }}
      >
        No chart data available to visualize
      </div>
    );
  }

  // Infer keys if not provided
  const sample = data[0];
  const detectedKeys = Object.keys(sample);
  const detectedXKey = x_key || detectedKeys[0] || 'name';
  const detectedYKey =
    y_key ||
    detectedKeys.find((k) => typeof sample[k] === 'number') ||
    detectedKeys[1] ||
    'value';

  const numericKeys =
    keys && keys.length > 0
      ? keys
      : detectedKeys.filter((k) => typeof sample[k] === 'number');

  const customTooltipStyle = {
    backgroundColor: '#0A0E1A',
    border: '1px solid rgba(0, 229, 255, 0.3)',
    borderRadius: '12px',
    boxShadow: '0 12px 36px -5px rgba(0, 0, 0, 0.7), 0 0 15px rgba(0, 229, 255, 0.1)',
    color: '#F8FAFC',
    fontSize: '0.82rem',
    fontFamily: "'Plus Jakarta Sans', sans-serif",
    padding: '10px 14px',
  };

  const axisColor = '#64748B';
  const gridColor = 'rgba(255, 255, 255, 0.05)';

  const formatAxisValue = (val: number) => {
    if (typeof val !== 'number') return val;
    if (Math.abs(val) >= 1_000_000_000) return `${(val / 1_000_000_000).toFixed(1)}B`;
    if (Math.abs(val) >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
    if (Math.abs(val) >= 1_000) return `${(val / 1_000).toFixed(0)}k`;
    return val.toString();
  };

  const renderContent = () => {
    switch (chart_type) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <AreaChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
              <defs>
                <linearGradient id="areaGradientPrimary" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00E5FF" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#00E5FF" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="areaGradientSecondary" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#A855F7" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#A855F7" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
              <XAxis
                dataKey={detectedXKey}
                stroke={axisColor}
                tick={{ fill: axisColor, fontSize: 11 }}
                tickLine={false}
              />
              <YAxis
                stroke={axisColor}
                tick={{ fill: axisColor, fontSize: 11 }}
                tickLine={false}
                tickFormatter={formatAxisValue}
              />
              <Tooltip contentStyle={customTooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
              {numericKeys.length > 0 ? (
                numericKeys.map((key, idx) => (
                  <Area
                    key={key}
                    type="monotone"
                    dataKey={key}
                    stroke={PALETTE[idx % PALETTE.length]}
                    strokeWidth={2.5}
                    fill="transparent"
                    dot={{ fill: PALETTE[idx % PALETTE.length], r: 3 }}
                    activeDot={{ r: 6, stroke: '#06080F', strokeWidth: 2 }}
                  />
                ))
              ) : (
                <Area
                  type="monotone"
                  dataKey={detectedYKey}
                  stroke="#00E5FF"
                  strokeWidth={2.5}
                  fill="transparent"
                  dot={{ fill: '#00E5FF', r: 3 }}
                  activeDot={{ r: 6, stroke: '#06080F', strokeWidth: 2 }}
                />
              )}
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'pie':
      case 'donut':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <PieChart>
              <Tooltip contentStyle={customTooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
              <Pie
                data={data}
                dataKey={detectedYKey}
                nameKey={detectedXKey}
                cx="50%"
                cy="50%"
                innerRadius={chart_type === 'donut' ? 64 : 0}
                outerRadius={95}
                paddingAngle={chart_type === 'donut' ? 4 : 2}
                stroke="#06080F"
                strokeWidth={2}
              >
                {data.map((entry, index) => {
                  const label = String(entry[detectedXKey] ?? '');
                  const color = CATEGORY_COLORS[label] || PALETTE[index % PALETTE.length];
                  return (
                    <Cell
                      key={`cell-${index}`}
                      fill={color}
                    />
                  );
                })}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        );

      case 'bar':
      default:
        return (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
              <XAxis
                dataKey={detectedXKey}
                stroke={axisColor}
                tick={{ fill: axisColor, fontSize: 11 }}
                tickLine={false}
              />
              <YAxis
                stroke={axisColor}
                tick={{ fill: axisColor, fontSize: 11 }}
                tickLine={false}
                tickFormatter={formatAxisValue}
              />
              <Tooltip contentStyle={customTooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
              {numericKeys.length > 0 && numericKeys.length > 1 ? (
                numericKeys.map((key, idx) => (
                  <Bar
                    key={key}
                    dataKey={key}
                    fill={PALETTE[idx % PALETTE.length]}
                    radius={[6, 6, 0, 0]}
                  />
                ))
              ) : (
                <Bar
                  dataKey={detectedYKey}
                  radius={[6, 6, 0, 0]}
                >
                  {data.map((entry, index) => {
                    const label = String(entry[detectedXKey] ?? '');
                    const color = CATEGORY_COLORS[label] || PALETTE[index % PALETTE.length];
                    return (
                      <Cell
                        key={`bar-cell-${index}`}
                        fill={color}
                      />
                    );
                  })}
                </Bar>
              )}
            </BarChart>
          </ResponsiveContainer>
        );
    }
  };

  return (
    <div className="card-base min-w-0 overflow-hidden flex flex-col justify-between">
      {title && (
        <h4 className="text-sm lg:text-base font-bold mb-4 text-white flex items-center gap-2.5 tracking-tight">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan shadow-[0_0_10px_#00E5FF] inline-block shrink-0" />
          <span className="truncate">{title}</span>
        </h4>
      )}
      <div className="w-full min-w-0 flex-1">
        {renderContent()}
      </div>
    </div>
  );
};

export default ChartRenderer;
