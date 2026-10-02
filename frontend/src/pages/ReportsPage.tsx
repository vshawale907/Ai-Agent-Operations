/* ============================================================================
   ReportsPage — Executive Business Operations & Intelligence Reports
   ============================================================================ */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Download,
  FileSpreadsheet,
  Sparkles,
  AlertTriangle,
  ShieldAlert,
  CheckCircle,
  RefreshCw,
  Calendar,
} from 'lucide-react';
import { reportsApi } from '../services/api';
import type { ExecutiveReportData } from '../types';

export const ReportsPage = () => {
  const [period, setPeriod] = useState('Trailing 12 Months');

  const { data, isLoading, refetch, isFetching } = useQuery<ExecutiveReportData>({
    queryKey: ['executive-report', period],
    queryFn: () => reportsApi.generate(period),
    staleTime: 120000,
  });

  const handleDownloadCsv = async () => {
    try {
      const blob = await reportsApi.exportCsv(period);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Executive_Report_${period.replace(/\s+/g, '_')}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('CSV download error:', err);
    }
  };

  const handleDownloadPdf = async () => {
    try {
      const blob = await reportsApi.exportPdf(period);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Executive_Report_${period.replace(/\s+/g, '_')}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('PDF download error:', err);
    }
  };

  const report = data;

  return (
    <div className="page-container">
      {/* ── Top Header & Actions ──────────────────────────────────────── */}
      <div className="section-header">
        <div>
          <div className="flex items-center gap-2 text-cyan font-mono text-[11px] font-semibold tracking-wider uppercase mb-1">
            <span className="w-2 h-2 rounded-full bg-cyan shadow-[0_0_8px_#00E5FF] animate-pulse" />
            Synthesis Engine
          </div>
          <h1 className="text-2xl md:text-3xl lg:text-4xl font-extrabold text-white tracking-tight">
            Executive Business Reports
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Automated executive intelligence synthesized from live financial data, operations, and anomalies
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <div className="relative">
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="bg-[#0E1424] border border-white/10 text-slate-200 rounded-xl h-11 pl-4 pr-9 text-xs font-semibold outline-none focus:border-cyan/50 focus:shadow-[0_0_15px_rgba(0,229,255,0.15)] transition-all cursor-pointer appearance-none"
            >
              <option value="Trailing 12 Months">Trailing 12 Months</option>
              <option value="Current Quarter YTD">Current Quarter YTD</option>
              <option value="Q3 2025 Performance">Q3 2025 Performance</option>
              <option value="Annual Fiscal Overview">Annual Fiscal Overview</option>
            </select>
            <Calendar size={14} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          </div>

          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-2 bg-[#0E1424] border border-white/10 text-slate-200 h-11 px-4 rounded-xl text-xs font-semibold cursor-pointer hover:border-cyan/40 hover:text-white hover:bg-cyan/[0.05] transition-all disabled:opacity-50"
          >
            <RefreshCw size={14} className={isFetching ? 'animate-spin' : ''} />
            <span>{isFetching ? 'Updating...' : 'Regenerate'}</span>
          </button>

          <button
            onClick={handleDownloadPdf}
            className="flex items-center gap-2 bg-gradient-to-r from-cyan via-[#00E5FF] to-violet text-black font-bold h-11 px-5 rounded-xl text-xs uppercase tracking-wider cursor-pointer shadow-[0_0_20px_rgba(0,229,255,0.25)] hover:shadow-[0_0_30px_rgba(0,229,255,0.45)] hover:-translate-y-0.5 transition-all"
          >
            <Download size={14} />
            <span>Download PDF</span>
          </button>

          <button
            onClick={handleDownloadCsv}
            className="flex items-center gap-2 bg-[#0E1424] border border-white/10 text-slate-200 h-11 px-4 rounded-xl text-xs font-semibold cursor-pointer hover:border-emerald-500/40 hover:text-emerald-400 hover:bg-emerald-500/5 transition-all"
          >
            <FileSpreadsheet size={15} className="text-emerald-400" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {isLoading && (
        <div className="text-center py-20 px-4 text-slate-400">
          <div className="w-10 h-10 border-2 border-cyan/30 border-t-cyan rounded-full animate-spin mx-auto mb-4" />
          <h3 className="text-white text-base font-semibold mb-1">
            Synthesizing Executive Report...
          </h3>
          <p className="text-xs md:text-sm text-slate-400 max-w-md mx-auto leading-relaxed">
            Compiling revenue trends, calculating customer LTV, analyzing margins, and scanning for statistical anomalies.
          </p>
        </div>
      )}

      {report && (
        <div className="card-container-lg flex flex-col gap-8 shadow-[0_16px_60px_-10px_rgba(0,0,0,0.8),0_0_0_1px_rgba(255,255,255,0.06)] animate-fade-in">
          {/* Document Header */}
          <div className="border-b border-white/[0.08] pb-6">
            <div className="flex items-center gap-2 text-cyan text-xs font-bold uppercase tracking-widest mb-2.5 font-mono">
              <Sparkles size={16} />
              <span>Official Executive Briefing</span>
            </div>
            <h2 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              {report.title}
            </h2>
            <div className="flex items-center gap-4 mt-3.5 text-xs text-slate-400 flex-wrap">
              <span className="flex items-center gap-1.5">
                <span className="text-slate-400">Period:</span>
                <strong className="text-slate-200 font-mono">{report.period}</strong>
              </span>
              <span className="text-slate-600">•</span>
              <span className="flex items-center gap-1.5">
                <span className="text-slate-400">Generated:</span>
                <strong className="text-slate-200 font-mono">{report.generated_at}</strong>
              </span>
              <span className="text-slate-600">•</span>
              <span className="text-cyan font-mono bg-cyan/10 border border-cyan/25 px-3 py-1 rounded-full text-[11px] font-semibold tracking-wide">
                Executive Confidential
              </span>
            </div>
          </div>

          {/* Section 1: Executive Summary */}
          <div>
            <h3 className="text-base font-bold text-white mb-3 tracking-tight">
              1. Executive Summary
            </h3>
            <p className="text-sm md:text-[15px] text-slate-200 leading-relaxed bg-white/[0.02] border border-white/[0.07] rounded-2xl p-6 md:p-7 shadow-inner">
              {report.executive_summary}
            </p>
          </div>

          {/* Operational Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {[
              { num: '02', title: 'Revenue Performance', content: report.revenue_performance },
              { num: '03', title: 'Customer Retention & LTV', content: report.customer_performance },
              { num: '04', title: 'Product Margins & Mix', content: report.product_performance },
              { num: '05', title: 'Cost Efficiency & OpEx', content: report.expense_performance },
            ].map(({ num, title, content }) => (
              <div
                key={num}
                className="bg-white/[0.02] border border-white/[0.07] rounded-2xl p-6 hover:border-cyan/30 hover:bg-white/[0.035] transition-all flex flex-col justify-between"
              >
                <div>
                  <h4 className="text-sm md:text-[15px] font-bold text-white mb-3 flex items-center gap-2">
                    <span className="text-cyan font-mono text-xs">{num}.</span>
                    <span>{title}</span>
                  </h4>
                  <p className="text-xs md:text-sm text-slate-300 leading-relaxed">{content}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Section: Anomalies Alert Box */}
          <div className="bg-gradient-to-r from-rose-950/40 via-rose-900/20 to-[#111726]/60 border border-rose-500/35 rounded-2xl p-6 md:p-7 shadow-[0_0_30px_rgba(244,63,94,0.12)]">
            <div className="flex items-center gap-3 text-rose-400 font-bold text-base md:text-lg mb-2.5">
              <AlertTriangle size={22} className="shrink-0 text-rose-400" />
              <span>Attention Required: Statistical Anomalies Detected</span>
            </div>
            <p className="text-xs md:text-sm text-rose-100/90 leading-relaxed font-medium">
              {report.anomalies_summary}
            </p>
          </div>

          {/* Strategic Insights */}
          <div>
            <h3 className="text-base font-bold text-white mb-3 tracking-tight">
              7. Strategic Operational Insights
            </h3>
            <div className="flex flex-col gap-2.5">
              {report.key_insights.map((insight, idx) => (
                <div
                  key={idx}
                  className="flex items-baseline gap-3.5 bg-white/[0.02] border border-white/[0.07] p-4 px-5 rounded-xl text-xs md:text-sm hover:border-cyan/25 transition-colors"
                >
                  <span className="text-cyan font-bold font-mono text-xs">0{idx + 1}.</span>
                  <span className="text-slate-200 leading-relaxed">{insight}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Risks & Recommendations Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Risks */}
            <div>
              <div className="flex items-center gap-2 text-rose-400 font-bold text-sm mb-3">
                <ShieldAlert size={17} />
                <span>8. Identified Operational Risks</span>
              </div>
              <div className="flex flex-col gap-2.5">
                {report.identified_risks.map((risk, idx) => (
                  <div
                    key={idx}
                    className="flex items-baseline gap-2.5 bg-rose-500/[0.08] border border-rose-500/20 p-3.5 px-4 rounded-xl text-xs md:text-sm text-rose-200 leading-relaxed"
                  >
                    <span className="text-rose-400 font-bold text-base leading-none">•</span>
                    <span>{risk}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommendations */}
            <div>
              <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm mb-3">
                <CheckCircle size={17} />
                <span>9. Recommended Areas for Investigation</span>
              </div>
              <div className="flex flex-col gap-2.5">
                {report.investigation_recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className="flex items-baseline gap-2.5 bg-emerald-500/[0.08] border border-emerald-500/20 p-3.5 px-4 rounded-xl text-xs md:text-sm text-emerald-200 leading-relaxed"
                  >
                    <span className="text-emerald-400 font-bold text-sm leading-none">✓</span>
                    <span>{rec}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportsPage;
