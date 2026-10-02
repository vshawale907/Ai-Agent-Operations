/* ============================================================================
   SQLViewer Component — Displays generated SQL with syntax styling & copy action
   ============================================================================ */

import { useState, type MouseEvent } from 'react';
import { Terminal, Copy, Check, Clock, Database, ChevronDown, ChevronUp } from 'lucide-react';

interface SQLViewerProps {
  sql: string;
  executionTimeMs?: number;
  rowCount?: number;
  dataSources?: string[];
  defaultOpen?: boolean;
}

export const SQLViewer = ({
  sql,
  executionTimeMs,
  rowCount,
  dataSources,
  defaultOpen = false,
}: SQLViewerProps) => {
  const [copied, setCopied] = useState(false);
  const [isOpen, setIsOpen] = useState(defaultOpen);

  const handleCopy = (e: MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-[#080C14] border border-white/[0.08] rounded-xl overflow-hidden mt-3 text-xs shadow-md">
      {/* Header Bar */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center justify-between h-10 px-4 bg-white/[0.03] cursor-pointer select-none transition-colors hover:bg-white/[0.05] ${
          isOpen ? 'border-b border-white/[0.07]' : ''
        }`}
      >
        <div className="flex items-center gap-2.5">
          <Terminal size={14} className="text-cyan" />
          <span className="font-semibold text-slate-300">Generated SQL Query</span>
          {executionTimeMs !== undefined && (
            <span className="inline-flex items-center gap-1 text-emerald-400 text-[11px] font-mono bg-emerald-500/10 border border-emerald-500/20 py-0.5 px-2 rounded-md font-semibold">
              <Clock size={11} />
              {executionTimeMs}ms
            </span>
          )}
          {rowCount !== undefined && (
            <span className="inline-flex items-center gap-1 text-cyan text-[11px] font-mono bg-cyan/10 border border-cyan/20 py-0.5 px-2 rounded-md font-semibold">
              <Database size={11} />
              {rowCount} rows
            </span>
          )}
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleCopy}
            title="Copy SQL Query"
            className={`flex items-center gap-1.5 bg-white/[0.05] hover:bg-white/[0.1] border border-white/10 rounded-lg py-1 px-2.5 cursor-pointer text-[11px] font-semibold transition-all duration-150 ${
              copied ? 'text-emerald-400 border-emerald-500/30' : 'text-slate-300'
            }`}
          >
            {copied ? <Check size={12} /> : <Copy size={12} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
          {isOpen ? <ChevronUp size={15} className="text-slate-400" /> : <ChevronDown size={15} className="text-slate-400" />}
        </div>
      </div>

      {/* Code Body */}
      {isOpen && (
        <div className="p-4 bg-[#05080F]/90 relative">
          <pre className="m-0 font-mono text-cyan-300 text-xs leading-relaxed whitespace-pre-wrap break-words overflow-x-auto">
            <code>{sql.trim()}</code>
          </pre>

          {dataSources && dataSources.length > 0 && (
            <div className="mt-3 pt-2.5 border-t border-white/[0.06] flex items-center gap-2 text-[11px] text-slate-400 flex-wrap">
              <span className="font-semibold text-slate-300">Data Sources:</span>
              {dataSources.map((ds) => (
                <span
                  key={ds}
                  className="bg-white/[0.04] border border-white/10 py-0.5 px-2 rounded-md text-slate-300 font-mono text-[10px]"
                >
                  {ds}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SQLViewer;
