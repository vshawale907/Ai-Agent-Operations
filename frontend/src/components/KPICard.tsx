/* ============================================================================
   KPICard Component — Futuristic glassmorphic KPI card with trend indicator
   ============================================================================ */

import type { ReactNode } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { KPI } from '../types';

interface KPICardProps {
  kpi: KPI;
  icon?: ReactNode;
  delay?: number;
}

export const KPICard = ({ kpi, icon, delay = 0 }: KPICardProps) => {
  const isPositive = (kpi.change_percent ?? 0) >= 0;
  const isUp = kpi.trend === 'up' || (kpi.trend === undefined && isPositive);
  const isNeutral = kpi.trend === 'stable' || kpi.change_percent === 0;

  const formatValue = (val: number) => {
    if (val >= 1_000_000_000) {
      return (val / 1_000_000_000).toFixed(2) + 'B';
    }
    if (val >= 1_000_000) {
      return (val / 1_000_000).toFixed(2) + 'M';
    }
    if (val >= 1_000) {
      return val.toLocaleString(undefined, { maximumFractionDigits: 2 });
    }
    return val.toString();
  };

  return (
    <div
      className="card-base hover:border-cyan/40 hover:shadow-[0_12px_36px_rgba(0,229,255,0.08)] hover:-translate-y-1 transition-all duration-300 relative overflow-hidden group flex flex-col justify-between min-w-0"
      style={{ animation: `fadeIn 0.35s ease-out ${delay * 0.06}s both` }}
    >
      {/* Top subtle glow highlight line */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-cyan/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className="text-xs font-bold text-slate-400 tracking-wider uppercase">
            {kpi.label}
          </span>
          {icon && (
            <div className="w-9 h-9 rounded-xl bg-white/[0.04] border border-white/[0.08] text-cyan flex items-center justify-center group-hover:bg-cyan/10 group-hover:border-cyan/30 transition-colors shrink-0">
              {icon}
            </div>
          )}
        </div>

        <div className="flex items-baseline gap-1.5 mb-3 font-mono flex-wrap">
          {kpi.prefix && (
            <span className="text-lg lg:text-xl text-slate-400 font-medium">{kpi.prefix}</span>
          )}
          <span className="text-2xl sm:text-3xl lg:text-2xl xl:text-3xl font-extrabold text-white tracking-tight truncate">
            {formatValue(kpi.value)}
          </span>
          {kpi.suffix && (
            <span className="text-xs text-slate-400 font-medium">{kpi.suffix}</span>
          )}
        </div>
      </div>

      {kpi.change_percent !== undefined ? (
        <div className="flex items-center gap-2 text-xs pt-1">
          <span
            className={`inline-flex items-center gap-1 font-semibold py-1 px-2.5 rounded-full border text-[11px] ${
              isNeutral
                ? 'bg-slate-500/10 text-slate-400 border-slate-500/20'
                : isUp
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25'
                : 'bg-rose-500/10 text-rose-400 border-rose-500/25'
            }`}
          >
            {isNeutral ? (
              <Minus size={12} />
            ) : isUp ? (
              <TrendingUp size={12} />
            ) : (
              <TrendingDown size={12} />
            )}
            {Math.abs(kpi.change_percent).toFixed(1)}%
          </span>
          <span className="text-slate-400 font-medium">vs prev period</span>
        </div>
      ) : (
        <div className="h-4" />
      )}
    </div>
  );
};

export default KPICard;
