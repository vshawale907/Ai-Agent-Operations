/* ============================================================================
   Analytics Page — In-Depth Revenue, Product, and Regional Exploration
   ============================================================================ */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart3,
  DollarSign,
  Package,
  Globe,
} from 'lucide-react';
import { analyticsApi } from '../services/api';
import ChartRenderer from '../components/ChartRenderer';
import DataTable from '../components/DataTable';

export const AnalyticsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'products' | 'regions' | 'financials'>('overview');
  const [timeframe, setTimeframe] = useState<'6m' | '12m'>('12m');

  const { data: revenueData, isLoading: revLoading, isError: revError } = useQuery({
    queryKey: ['analytics-revenue', timeframe],
    queryFn: () => analyticsApi.getRevenue(timeframe === '6m' ? 6 : 12),
  });

  const { data: productsData, isLoading: prodLoading, isError: prodError } = useQuery({
    queryKey: ['analytics-products'],
    queryFn: () => analyticsApi.getProducts(),
  });

  const { data: regionsData, isLoading: regLoading, isError: regError } = useQuery({
    queryKey: ['analytics-regions'],
    queryFn: () => analyticsApi.getRegions(),
  });

  const revenueList = (revenueData as any)?.monthly_data || (Array.isArray(revenueData) ? revenueData : []);
  const productList = (productsData as any)?.products || (Array.isArray(productsData) ? productsData : []);
  const regionList = (regionsData as any)?.regions || (Array.isArray(regionsData) ? regionsData : []);

  const isLoading = revLoading || prodLoading || regLoading;
  const isError = revError || prodError || regError;

  const tabs = [
    { id: 'overview', label: 'Overview & Trends', icon: BarChart3 },
    { id: 'products', label: 'Product Performance', icon: Package },
    { id: 'regions', label: 'Regional Geography', icon: Globe },
    { id: 'financials', label: 'Financial Margins', icon: DollarSign },
  ];

  return (
    <div className="page-container">
      {/* Page Header */}
      <div className="section-header">
        <div>
          <div className="flex items-center gap-2 text-cyan font-mono text-[11px] font-semibold tracking-wider uppercase mb-1">
            <span className="w-2 h-2 rounded-full bg-cyan shadow-[0_0_8px_#00E5FF] animate-pulse" />
            Executive Deep Dive
          </div>
          <h1 className="text-2xl md:text-3xl lg:text-4xl font-extrabold text-white tracking-tight">
            Analytics & Business Intelligence
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Exploratory intelligence across financial performance, product lines, and global territories
          </p>
        </div>

        {/* Timeframe selector */}
        <div className="flex items-center gap-1.5 bg-[#0E1424] p-1.5 rounded-xl border border-white/10 shrink-0">
          <button
            onClick={() => setTimeframe('6m')}
            className={`py-2 px-4 rounded-lg border text-xs font-semibold cursor-pointer transition-all duration-150 ${
              timeframe === '6m'
                ? 'bg-cyan/15 text-cyan border-cyan/30 shadow-[0_0_12px_rgba(0,229,255,0.2)]'
                : 'bg-transparent border-transparent text-slate-400 hover:text-white'
            }`}
          >
            Last 6 Months
          </button>
          <button
            onClick={() => setTimeframe('12m')}
            className={`py-2 px-4 rounded-lg border text-xs font-semibold cursor-pointer transition-all duration-150 ${
              timeframe === '12m'
                ? 'bg-cyan/15 text-cyan border-cyan/30 shadow-[0_0_12px_rgba(0,229,255,0.2)]'
                : 'bg-transparent border-transparent text-slate-400 hover:text-white'
            }`}
          >
            Last 12 Months
          </button>
        </div>
      </div>

      {/* Tabs navigation */}
      <div className="flex gap-2.5 border-b border-white/[0.08] pb-3.5 overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id as any)}
            className={`flex items-center gap-2.5 py-2.5 px-4.5 rounded-xl border text-xs font-semibold cursor-pointer transition-all duration-150 whitespace-nowrap shrink-0 ${
              activeTab === id
                ? 'bg-cyan/10 text-cyan border-cyan/30 shadow-[0_0_15px_rgba(0,229,255,0.12)]'
                : 'bg-transparent border-transparent text-slate-400 hover:text-white hover:bg-white/[0.04]'
            }`}
          >
            <Icon size={16} />
            <span>{label}</span>
          </button>
        ))}
      </div>

      {/* States */}
      {isLoading && (
        <div className="card-base flex items-center justify-center py-20 text-cyan">
          <div className="w-6 h-6 border-2 border-cyan/30 border-t-cyan rounded-full animate-spin" />
          <span className="ml-3 font-semibold text-lg">Loading analytics data...</span>
        </div>
      )}

      {isError && (
        <div className="card-base border-rose-500/30 bg-rose-500/5 text-center py-10">
          <h3 className="text-xl font-bold text-rose-400 mb-2">Failed to load analytics</h3>
          <p className="text-slate-400">Please try again later or check your connection.</p>
        </div>
      )}

      {/* Tab Content */}
      {!isLoading && !isError && activeTab === 'overview' && (
        <div className="flex flex-col gap-6">
          <div className="chart-grid">
            <ChartRenderer
              chartData={{
                chart_type: 'line',
                title: 'Revenue vs Operating Expenses',
                data: revenueList,
                x_key: 'month_label',
                keys: ['revenue', 'expenses', 'net_margin'],
              }}
              height={340}
            />

            <ChartRenderer
              chartData={{
                chart_type: 'bar',
                title: 'Monthly Order Volume',
                data: revenueList,
                x_key: 'month_label',
                y_key: 'orders',
              }}
              height={340}
            />
          </div>

          <div className="card-base">
            <h3 className="text-base font-bold text-white mb-3">
              Monthly Performance Records
            </h3>
            <DataTable data={revenueList} pageSize={6} />
          </div>
        </div>
      )}

      {!isLoading && !isError && activeTab === 'products' && (
        <div className="flex flex-col gap-6">
          <ChartRenderer
            chartData={{
              chart_type: 'bar',
              title: 'Revenue by Product SKU ($ USD)',
              data: productList.map((p: any) => ({
                Product: p.name,
                Revenue: p.revenue,
              })),
              x_key: 'Product',
              y_key: 'Revenue',
            }}
            height={340}
          />

          <div className="card-base">
            <h3 className="text-base font-bold text-white mb-3">
              Full Product Catalog Performance
            </h3>
            <DataTable data={productList} pageSize={8} />
          </div>
        </div>
      )}

      {!isLoading && !isError && activeTab === 'regions' && (
        <div className="flex flex-col gap-6">
          <div className="chart-grid">
            <ChartRenderer
              chartData={{
                chart_type: 'donut',
                title: 'Market Share by Territory',
                data: regionList.map((r: any) => ({
                  name: r.region,
                  value: r.revenue,
                })),
                x_key: 'name',
                y_key: 'value',
              }}
              height={340}
            />

            <ChartRenderer
              chartData={{
                chart_type: 'bar',
                title: 'Average Order Value by Region ($)',
                data: regionList.map((r: any) => ({
                  Region: r.region,
                  AOV: r.avg_order_value,
                })),
                x_key: 'Region',
                y_key: 'AOV',
              }}
              height={340}
            />
          </div>

          <div className="card-base">
            <h3 className="text-base font-bold text-white mb-3">
              Territory Breakdown Summary
            </h3>
            <DataTable data={regionList} pageSize={5} />
          </div>
        </div>
      )}

      {!isLoading && !isError && activeTab === 'financials' && (
        <div className="flex flex-col gap-6">
          <ChartRenderer
            chartData={{
              chart_type: 'line',
              title: 'Net Margin Growth Trend',
              data: revenueList.map((r: any) => ({
                month: r.month_label,
                'Net Margin': r.net_margin,
              })),
              x_key: 'month',
              y_key: 'Net Margin',
            }}
            height={340}
          />

          <div className="card-base">
            <h3 className="text-base font-bold text-white mb-3">
              Financial Breakdown Table
            </h3>
            <DataTable data={revenueList} pageSize={6} />
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalyticsPage;
