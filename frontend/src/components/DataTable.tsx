/* ============================================================================
   DataTable Component — Elegant tabular display for structured query results
   ============================================================================ */

import { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface DataTableProps {
  data: Record<string, unknown>[];
  pageSize?: number;
}

export const DataTable = ({ data, pageSize = 8 }: DataTableProps) => {
  const [currentPage, setCurrentPage] = useState(1);

  if (!data || data.length === 0) {
    return (
      <div className="p-6 text-slate-400 text-sm text-center">
        No table data to display.
      </div>
    );
  }

  const columns = Object.keys(data[0]);
  const totalPages = Math.ceil(data.length / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const currentRows = data.slice(startIndex, startIndex + pageSize);

  const formatCellValue = (val: unknown): string => {
    if (val === null || val === undefined) return '-';
    if (typeof val === 'number') {
      return Number.isInteger(val) ? val.toLocaleString() : val.toFixed(2);
    }
    if (typeof val === 'boolean') return val ? 'Yes' : 'No';
    if (typeof val === 'object') return JSON.stringify(val);
    return String(val);
  };

  const isNumericLike = (val: unknown): boolean => {
    if (typeof val === 'number') return true;
    if (typeof val === 'string' && val.length > 0) {
      return !isNaN(Number(val.replace(/[^0-9.-]+/g, '')));
    }
    return false;
  };

  const renderStatusBadge = (val: string) => {
    const lower = val.toLowerCase();
    if (lower === 'completed' || lower === 'active' || lower === 'success') {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          {val}
        </span>
      );
    }
    if (lower === 'shipped' || lower === 'in_transit') {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan/10 text-cyan border border-cyan/20">
          {val}
        </span>
      );
    }
    if (lower === 'processing' || lower === 'pending') {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
          {val}
        </span>
      );
    }
    if (lower === 'failed' || lower === 'cancelled' || lower === 'blocked') {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
          {val}
        </span>
      );
    }
    return null;
  };

  return (
    <div className="w-full mt-4 rounded-2xl border border-white/[0.08] overflow-hidden bg-[#0A0E1A]/95 backdrop-blur-md shadow-lg">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-white/[0.08] bg-white/[0.03]">
              {columns.map((col) => (
                <th
                  key={col}
                  className="py-3.5 px-5 text-slate-400 text-xs font-bold uppercase tracking-wider whitespace-nowrap"
                >
                  {col.replace(/_/g, ' ')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {currentRows.map((row, rIdx) => (
              <tr
                key={rIdx}
                className={`transition-colors duration-150 hover:bg-white/[0.035] ${
                  rIdx < currentRows.length - 1 ? 'border-b border-white/[0.05]' : ''
                }`}
              >
                {columns.map((col) => {
                  const val = row[col];
                  const stringVal = String(val ?? '');
                  const statusBadge = col.toLowerCase().includes('status')
                    ? renderStatusBadge(stringVal)
                    : null;

                  return (
                    <td
                      key={col}
                      className={`py-3.5 px-5 text-slate-200 whitespace-nowrap text-sm ${
                        isNumericLike(val) ? 'font-mono text-cyan-300 font-medium' : ''
                      }`}
                    >
                      {statusBadge || formatCellValue(val)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between py-3.5 px-5 border-t border-white/[0.08] text-xs text-slate-400 bg-white/[0.01]">
          <span>
            Showing {startIndex + 1} to {Math.min(startIndex + pageSize, data.length)} of{' '}
            {data.length} entries
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              aria-label="Previous Page"
              className={`w-8 h-8 rounded-lg border border-white/10 bg-white/[0.04] transition-colors flex items-center justify-center cursor-pointer ${
                currentPage === 1
                  ? 'text-slate-600 border-white/5 cursor-not-allowed'
                  : 'text-slate-300 hover:text-cyan hover:border-cyan/40 hover:bg-cyan/10'
              }`}
            >
              <ChevronLeft size={15} />
            </button>
            <span className="font-mono px-2 text-slate-300">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              aria-label="Next Page"
              className={`w-8 h-8 rounded-lg border border-white/10 bg-white/[0.04] transition-colors flex items-center justify-center cursor-pointer ${
                currentPage === totalPages
                  ? 'text-slate-600 border-white/5 cursor-not-allowed'
                  : 'text-slate-300 hover:text-cyan hover:border-cyan/40 hover:bg-cyan/10'
              }`}
            >
              <ChevronRight size={15} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataTable;
