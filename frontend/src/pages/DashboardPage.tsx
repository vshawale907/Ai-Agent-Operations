/* ============================================================================
   Dashboard Page — Executive Business Overview & Performance Indicators
   ============================================================================ */

import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  DollarSign,
  ShoppingCart,
  Users,
  TrendingUp,
  Sparkles,
  ArrowRight,
  Package,
  RefreshCw,
} from 'lucide-react';
import { analyticsApi } from '../services/api';
import type { DashboardData, KPI } from '../types';
import KPICard from '../components/KPICard';
import ChartRenderer from '../components/ChartRenderer';
import DataTable from '../components/DataTable';

// High-fidelity fallback data in case database is cold/loading
// @ts-ignore – reserved for future fallback rendering; not yet wired up
const _FALLBACK_DASHBOARD: DashboardData = {
  kpis: [
    { label: 'Total Revenue', value: 142580, change_percent: 12.4, trend: 'up', prefix: '$' },
    { label: 'Total Orders', value: 1840, change_percent: 8.1, trend: 'up' },
    { label: 'Avg Order Value', value: 77.49, change_percent: 4.2, trend: 'up', prefix: '$' },
    { label: 'Active Customers', value: 620, change_percent: -1.5, trend: 'down' },
  ],
  monthly_revenue: [
    { month: '2025-05', month_label: 'May', revenue: 19800, order_count: 245 },
    { month: '2025-06', month_label: 'Jun', revenue: 21500, order_count: 270 },
    { month: '2025-07', month_label: 'Jul', revenue: 24200, order_count: 310 },
    { month: '2025-08', month_label: 'Aug', revenue: 22900, order_count: 295 },
    { month: '2025-09', month_label: 'Sep', revenue: 26800, order_count: 340 },
    { month: '2025-10', month_label: 'Oct', revenue: 27380, order_count: 380 },
  ],
  revenue_by_region: [
    { region: 'North America', revenue: 64200, order_count: 820, avg_order_value: 78.29 },
    { region: 'Europe', revenue: 41800, order_count: 540, avg_order_value: 77.41 },
    { region: 'Asia Pacific', revenue: 25400, order_count: 330, avg_order_value: 76.97 },
    { region: 'Latin America', revenue: 11180, order_count: 150, avg_order_value: 74.53 },
  ],
  top_products: [
    { name: 'Enterprise Cloud AI Suite', category: 'Software', revenue: 42500, units_sold: 85, order_count: 85 },
    { name: 'Analytics Pro License', category: 'Software', revenue: 28900, units_sold: 190, order_count: 180 },
    { name: 'Data Pipeline Hub', category: 'Platform', revenue: 22100, units_sold: 70, order_count: 68 },
    { name: 'Security & Compliance Pack', category: 'Security', revenue: 18400, units_sold: 92, order_count: 90 },
    { name: 'Operations Automation Tool', category: 'Automation', revenue: 15680, units_sold: 120, order_count: 115 },
  ],
  revenue_by_category: [
    { category: 'Software', revenue: 71400, units_sold: 275, order_count: 265 },
    { category: 'Platform', revenue: 35200, units_sold: 110, order_count: 105 },
    { category: 'Security', revenue: 21600, units_sold: 108, order_count: 102 },
    { category: 'Automation', revenue: 14380, units_sold: 115, order_count: 110 },
  ],
  expense_trend: [
    { month: '2025-05', month_label: 'May', total_expense: 11200 },
    { month: '2025-06', month_label: 'Jun', total_expense: 12400 },
    { month: '2025-07', month_label: 'Jul', total_expense: 13100 },
    { month: '2025-08', month_label: 'Aug', total_expense: 12800 },
    { month: '2025-09', month_label: 'Sep', total_expense: 14200 },
    { month: '2025-10', month_label: 'Oct', total_expense: 14900 },
  ],
  recent_orders: [
    { id: 1024, customer: 'Acme Corp', region: 'North America', amount: 1420.0, date: '2025-10-24', status: 'completed' },
    { id: 1023, customer: 'Global Logix', region: 'Europe', amount: 3890.5, date: '2025-10-24', status: 'completed' },
    { id: 1022, customer: 'Apex Data Inc', region: 'Asia Pacific', amount: 820.0, date: '2025-10-23', status: 'processing' },
    { id: 1021, customer: 'Zenith Retail', region: 'North America', amount: 2450.0, date: '2025-10-23', status: 'completed' },
    { id: 1020, customer: 'Starlight Media', region: 'Latin America', amount: 950.0, date: '2025-10-22', status: 'shipped' },
  ],
};

const SUGGESTED_QUESTIONS = [
  'What was our revenue last month?',
  'What are our top 5 products by revenue?',
  'Which region generated the most revenue?',
  'Compare monthly revenue trends with expenses',
];

export const DashboardPage = () => {
  const navigate = useNavigate();

  const { data, isFetching, error, refetch, isError } = useQuery({
    queryKey: ['dashboard-overview'],
    queryFn: async () => {
      const res = await analyticsApi.getDashboard();
      return res;
    },
    staleTime: 60000,
  });

  const dashboardData = data;

  const handleAskAI = (question: string) => {
    navigate('/ai', { state: { prefilledQuestion: question } });
  };

  const getKPIIcon = (kpi: KPI, index: number) => {
    const label = kpi.label.toLowerCase();
    if (label.includes('revenue') && !label.includes('growth')) {
      return <DollarSign size={18} className="text-cyan" />;
    }
    if (label.includes('order')) {
      return <ShoppingCart size={18} className="text-emerald-400" />;
    }
    if (label.includes('customer') || label.includes('user')) {
      return <Users size={18} className="text-violet-400" />;
    }
    if (label.includes('growth') || label.includes('trend') || label.includes('rate') || label.includes('value')) {
      return <TrendingUp size={18} className="text-amber-400" />;
    }
    if (index === 0) return <DollarSign size={18} className="text-cyan" />;
    if (index === 1) return <ShoppingCart size={18} className="text-emerald-400" />;
    if (index === 2) return <Users size={18} className="text-violet-400" />;
    return <TrendingUp size={18} className="text-amber-400" />;
  };

  return (
    <div className="page-container">
      {/* ── Section 1: Page Header ──────────────────────────────────── */}
      <div className="section-header">
        <div>
          <div className="flex items-center gap-2 text-cyan font-mono text-[11px] font-semibold tracking-wider uppercase mb-1">
            <span className="w-2 h-2 rounded-full bg-cyan shadow-[0_0_8px_#00E5FF] animate-pulse" />
            Live Operations Feed
          </div>
          <h1 className="text-2xl md:text-3xl lg:text-4xl font-extrabold text-white tracking-tight">
            Operations & Analytics Dashboard
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Real-time business performance overview powered by autonomous AI intelligence
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-2 bg-[#0E1424] border border-white/10 text-slate-200 h-11 px-4 rounded-xl text-xs font-semibold cursor-pointer transition-all duration-200 hover:border-cyan/40 hover:text-white hover:bg-cyan/[0.05] disabled:opacity-50"
          >
            <RefreshCw size={14} className={isFetching ? 'animate-spin' : ''} />
            <span>{isFetching ? 'Refreshing...' : 'Refresh'}</span>
          </button>

          <button
            onClick={() => navigate('/ai')}
            className="flex items-center gap-2 bg-gradient-to-r from-cyan via-[#00E5FF] to-violet text-black font-bold h-11 px-5 rounded-xl text-xs uppercase tracking-wider cursor-pointer shadow-[0_0_20px_rgba(0,229,255,0.25)] hover:shadow-[0_0_30px_rgba(0,229,255,0.45)] hover:-translate-y-0.5 transition-all duration-150"
          >
            <Sparkles size={15} />
            <span>Ask AI Agent</span>
          </button>
        </div>
      </div>

      {isFetching && !dashboardData && (
        <div className="card-base flex items-center justify-center py-20 text-cyan">
          <RefreshCw size={24} className="animate-spin" />
          <span className="ml-3 font-semibold text-lg">Loading dashboard data...</span>
        </div>
      )}

      {isError && (
        <div className="card-base border-rose-500/30 bg-rose-500/5 text-center py-10">
          <h3 className="text-xl font-bold text-rose-400 mb-2">Failed to load dashboard</h3>
          <p className="text-slate-400">{(error as any)?.message || 'An error occurred while fetching data.'}</p>
        </div>
      )}

      {dashboardData && (
        <>
      {/* ── Section 2: AI Insights ──────────────────────────────────── */}
      <div className="card-base p-5 md:p-6">
        <div className="flex items-center gap-2.5 mb-3.5">
          <div className="p-2 rounded-xl bg-cyan/10 border border-cyan/25 text-cyan shadow-[0_0_12px_rgba(0,229,255,0.15)]">
            <Sparkles size={16} />
          </div>
          <span className="text-sm font-bold text-white tracking-wide uppercase">
            Instant AI Insights
          </span>
        </div>

        <div className="flex flex-wrap gap-2.5">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => handleAskAI(q)}
              className="bg-white/[0.03] border border-white/[0.08] rounded-xl text-slate-300 py-2.5 px-4 text-xs font-medium cursor-pointer inline-flex items-center gap-2 transition-all duration-150 hover:text-cyan hover:border-cyan/40 hover:bg-cyan/10"
            >
              <span>{q}</span>
              <ArrowRight size={12} className="text-cyan opacity-70 shrink-0" />
            </button>
          ))}
        </div>
      </div>

      {/* ── Section 3: KPI Cards Grid (5-column balanced) ───────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5">
        {dashboardData.kpis.map((kpi: KPI, index: number) => (
          <div
            key={kpi.label}
            className={`min-w-0 ${index === 4 ? 'sm:col-span-2 lg:col-span-1' : ''}`}
          >
            <KPICard kpi={kpi} icon={getKPIIcon(kpi, index)} delay={index} />
          </div>
        ))}
      </div>

      {/* ── Section 4: Analytics Charts Row 1 ──────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <ChartRenderer
          chartData={{
            chart_type: 'line',
            title: 'Monthly Revenue Trend ($ USD)',
            data: dashboardData.monthly_revenue.map((m: any) => ({
              month: m.month_label,
              Revenue: m.revenue,
            })),
            x_key: 'month',
            y_key: 'Revenue',
          }}
          height={340}
        />

        <ChartRenderer
          chartData={{
            chart_type: 'donut',
            title: 'Revenue Distribution by Category',
            data: dashboardData.revenue_by_category.map((c: any) => ({
              name: c.category,
              value: c.revenue,
            })),
            x_key: 'name',
            y_key: 'value',
          }}
          height={340}
        />
      </div>

      {/* ── Section 5: Analytics Charts Row 2 ──────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <ChartRenderer
          chartData={{
            chart_type: 'bar',
            title: 'Revenue by Geographic Region ($ USD)',
            data: dashboardData.revenue_by_region.map((r: any) => ({
              Region: r.region,
              Revenue: r.revenue,
            })),
            x_key: 'Region',
            y_key: 'Revenue',
          }}
          height={340}
        />

        <ChartRenderer
          chartData={{
            chart_type: 'bar',
            title: 'Top Performing Products ($ Revenue)',
            data: dashboardData.top_products.map((p: any) => ({
              Product: p.name.length > 22 ? p.name.slice(0, 22) + '...' : p.name,
              Revenue: p.revenue,
            })),
            x_key: 'Product',
            y_key: 'Revenue',
          }}
          height={340}
        />
      </div>

      {/* ── Section 6: Recent Orders Table ──────────────────────────── */}
      <div className="card-base">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-cyan/10 border border-cyan/20 text-cyan">
              <Package size={17} />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">
                Recent Completed Orders
              </h3>
              <p className="text-xs text-slate-400">Latest transactions stream across regions</p>
            </div>
          </div>
          <span className="text-xs text-cyan font-mono bg-cyan/10 border border-cyan/20 px-2.5 py-1 rounded-full">
            Live Database Sync
          </span>
        </div>

        <DataTable
          data={dashboardData.recent_orders.map((o: any) => ({
            'Order #': `#${o.id}`,
            Customer: o.customer,
            Region: o.region,
            Amount: `$${o.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
            Date: o.date,
            Status: o.status,
          }))}
          pageSize={5}
        />
      </div>
      </>
      )}
    </div>
  );
};

export default DashboardPage;
