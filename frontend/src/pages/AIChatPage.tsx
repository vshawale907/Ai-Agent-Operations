/* ============================================================================
   AIChatPage — Core Conversational Analytics Agent Interface
   ============================================================================ */

import { useState, useEffect, useRef, type ReactNode } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Send,
  Sparkles,
  Bot,
  User as UserIcon,
  Trash2,
  Table as TableIcon,
  BookOpen,
  ArrowRight,
} from 'lucide-react';
import { chatApi } from '../services/api';
import type { ChatMessage } from '../types';
import ChartRenderer from '../components/ChartRenderer';
import SQLViewer from '../components/SQLViewer';
import DataTable from '../components/DataTable';

const SAMPLE_QUESTIONS = [
  'What was our total revenue last month?',
  'What is our enterprise refund policy?',
  'What are our top 5 products by revenue?',
  'Why did revenue decline according to our sales strategy document?',
  'Detect any recent operational anomalies in our business',
  'What are our customer churn risk indicators and LTV?',
];

const WELCOME_MESSAGE: ChatMessage = {
  id: 'welcome',
  role: 'assistant',
  content: `Hello! I am your **Autonomous Business Operations & Analytics Agent**.

I can directly analyze your company's live database, generate and validate read-only SQL queries, calculate business performance metrics, and synthesize strategic insights for executive decisions.

**Try asking me:**
• "What was our revenue last month?"
• "What are our top 5 products by revenue?"
• "Which region generated the most revenue?"
• "Show me the breakdown of sales by category."`,
  timestamp: new Date().toISOString(),
};

/**
 * Parses inline markdown: **bold**, *italic*, `code`, and clean quotes.
 */
function parseInline(text: string): ReactNode[] {
  // Regex to match **bold**, *italic*, `code`
  const regex = /(\*\*.*?\*\*|\*.*?\*|`.*?`)/g;
  const parts = text.split(regex);

  return parts.map((part, idx) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={idx} className="font-semibold text-white">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith('*') && part.endsWith('*') && part.length > 2) {
      return (
        <em key={idx} className="italic text-cyan-200">
          {part.slice(1, -1)}
        </em>
      );
    }
    if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
      return (
        <code
          key={idx}
          className="font-mono text-xs bg-white/[0.08] text-cyan px-1.5 py-0.5 rounded border border-white/10"
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

/**
 * Rich markdown block renderer for AI responses:
 * Handles titles, bullet lists, numbered items, quotes, and paragraphs cleanly.
 */
function renderFormattedContent(content: string) {
  const lines = content.split('\n');
  const elements: ReactNode[] = [];
  let currentList: { type: 'ul' | 'ol'; items: string[] } | null = null;

  const flushList = () => {
    if (!currentList) return;
    if (currentList.type === 'ul') {
      elements.push(
        <ul key={`ul-${elements.length}`} className="my-2.5 space-y-1.5 pl-4 list-disc marker:text-cyan text-slate-200 text-sm">
          {currentList.items.map((item, i) => (
            <li key={i} className="leading-relaxed">
              {parseInline(item)}
            </li>
          ))}
        </ul>
      );
    } else {
      elements.push(
        <ol key={`ol-${elements.length}`} className="my-2.5 space-y-1.5 pl-5 list-decimal marker:text-cyan font-mono text-slate-200 text-xs">
          {currentList.items.map((item, i) => (
            <li key={i} className="font-sans text-sm leading-relaxed">
              {parseInline(item)}
            </li>
          ))}
        </ol>
      );
    }
    currentList = null;
  };

  lines.forEach((rawLine, idx) => {
    const line = rawLine.trim();

    // Check for bullet list
    if (line.startsWith('• ') || line.startsWith('* ') || line.startsWith('- ')) {
      const cleanItem = line.replace(/^[•*-]\s+/, '').replace(/^["']|["']$/g, '');
      if (!currentList || currentList.type !== 'ul') {
        flushList();
        currentList = { type: 'ul', items: [] };
      }
      currentList.items.push(cleanItem);
      return;
    }

    // Check for numbered list
    const numMatch = line.match(/^(\d+)\.\s+(.*)/);
    if (numMatch) {
      if (!currentList || currentList.type !== 'ol') {
        flushList();
        currentList = { type: 'ol', items: [] };
      }
      currentList.items.push(numMatch[2]);
      return;
    }

    // Not in a list, flush any active list
    flushList();

    if (!line) {
      elements.push(<div key={`spacer-${idx}`} className="h-2" />);
      return;
    }

    // Headers: ### Header
    if (line.startsWith('### ')) {
      elements.push(
        <h4 key={`h4-${idx}`} className="text-sm font-bold text-white mt-3.5 mb-1.5 tracking-tight flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan" />
          <span>{parseInline(line.slice(4))}</span>
        </h4>
      );
      return;
    }
    if (line.startsWith('## ') || line.startsWith('# ')) {
      elements.push(
        <h3 key={`h3-${idx}`} className="text-base font-bold text-white mt-4 mb-2 tracking-tight">
          {parseInline(line.replace(/^#+\s+/, ''))}
        </h3>
      );
      return;
    }

    // Bold title lines: **Title** or **Title:**
    if (line.startsWith('**') && (line.endsWith('**') || line.endsWith('**:'))) {
      elements.push(
        <p key={`title-${idx}`} className="font-bold text-white mt-3 mb-1 text-sm tracking-wide">
          {parseInline(line)}
        </p>
      );
      return;
    }

    // Normal paragraph
    elements.push(
      <p key={`p-${idx}`} className="my-1.5 text-slate-200 leading-relaxed text-sm">
        {parseInline(line)}
      </p>
    );
  });

  flushList();
  return elements;
}

export const AIChatPage: React.FC = () => {
  const location = useLocation();
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeStep, setActiveStep] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Handle prefilled question from navigation (e.g. from Dashboard)
  useEffect(() => {
    const prefilled = (location.state as any)?.prefilledQuestion;
    if (prefilled) {
      handleSendMessage(prefilled);
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query || isLoading) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setActiveStep('Analyzing question context...');

    const stepTimer1 = setTimeout(() => {
      setActiveStep('Querying verified PostgreSQL warehouse...');
    }, 600);
    const stepTimer2 = setTimeout(() => {
      setActiveStep('Validating schema and data records...');
    }, 1400);
    const stepTimer3 = setTimeout(() => {
      setActiveStep('Synthesizing executive business insights...');
    }, 2200);

    try {
      const response = await chatApi.send({
        message: query,
        conversation_id: conversationId,
      });
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      clearTimeout(stepTimer3);

      if (response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.message,
        timestamp: new Date().toISOString(),
        metadata: {
          sql_query: response.metadata?.sql_query,
          execution_time_ms: response.metadata?.execution_time_ms,
          data_sources: response.metadata?.data_sources,
          row_count: response.table_data?.length,
        },
        chart_data: response.chart_data,
        table_data: response.table_data,
        citations: response.citations,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      clearTimeout(stepTimer3);
      console.error('Chat API request failed:', err);

      const errorDetail =
        err?.response?.data?.detail ||
        err?.message ||
        'Unable to complete request. Please verify server connectivity.';

      const errorAssistantMessage: ChatMessage = {
        id: `assistant-error-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ **Inquiry Execution Notice**\n\nCould not retrieve data from the server: ${errorDetail}\n\nPlease try again or rephrase your question.`,
        timestamp: new Date().toISOString(),
        metadata: {
          data_sources: ['PostgreSQL Warehouse Error Handler'],
        },
      };

      setMessages((prev) => [...prev, errorAssistantMessage]);
    } finally {
      setIsLoading(false);
      setActiveStep(null);
    }
  };

  const handleClearHistory = () => {
    setMessages([WELCOME_MESSAGE]);
    setConversationId(undefined);
  };

  return (
    <div className="w-full flex flex-col gap-4 h-[calc(100vh-4.5rem)] min-w-0">
      {/* ── Section Header ────────────────────────────────────────────── */}
      <div className="flex items-center justify-between pb-3.5 border-b border-white/[0.08] flex-wrap gap-3">
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan via-[#00E5FF] to-violet flex items-center justify-center shadow-[0_0_20px_rgba(0,229,255,0.35)] shrink-0 ring-1 ring-white/20">
            <Sparkles size={20} className="text-black" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2 tracking-tight">
              AI Business Operations Agent
            </h2>
            <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#10B981] animate-pulse" />
              <span>Connected to Read-Only High-Speed Analytics Engine</span>
            </div>
          </div>
        </div>

        <button
          onClick={handleClearHistory}
          className="flex items-center gap-2 bg-[#0E1424] border border-white/10 text-slate-300 h-9 px-3.5 rounded-xl text-xs font-semibold cursor-pointer transition-all duration-150 hover:text-rose-400 hover:border-rose-500/30 hover:bg-rose-500/10"
        >
          <Trash2 size={14} />
          <span>Clear Chat</span>
        </button>
      </div>

      {/* ── Suggested Question Chips ─────────────────────────────────── */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden flex-nowrap">
        {SAMPLE_QUESTIONS.map((q) => (
          <button
            key={q}
            onClick={() => handleSendMessage(q)}
            disabled={isLoading}
            className="whitespace-nowrap bg-[#0E1424] border border-white/[0.08] rounded-xl h-8 px-3.5 text-slate-300 text-xs font-medium cursor-pointer flex items-center gap-1.5 transition-all duration-150 hover:text-cyan hover:border-cyan/40 hover:bg-cyan/[0.06] disabled:opacity-50 shrink-0 shadow-sm"
          >
            <span>{q}</span>
            <ArrowRight size={11} className="text-cyan/60 shrink-0" />
          </button>
        ))}
      </div>

      {/* ── Messages Scroll Area ─────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto flex flex-col gap-6 pr-2">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={msg.id}
              className={`flex gap-3.5 items-start animate-fade-in ${
                isUser ? 'flex-row-reverse' : 'flex-row'
              }`}
            >
              {/* Avatar Icon */}
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 shadow-md ${
                  isUser
                    ? 'bg-gradient-to-tr from-cyan via-[#00E5FF] to-violet text-black font-bold ring-1 ring-white/20'
                    : 'bg-[#0E1424] border border-cyan/40 text-cyan shadow-[0_0_12px_rgba(0,229,255,0.2)]'
                }`}
              >
                {isUser ? <UserIcon size={17} /> : <Bot size={17} />}
              </div>

              {/* Message Bubble & Metadata */}
              <div className="max-w-[84%] flex flex-col gap-1.5">
                <div
                  className={`p-4 md:p-5 text-sm ${
                    isUser
                      ? 'bg-gradient-to-r from-cyan-400 to-[#00D0EB] text-slate-950 font-semibold rounded-2xl rounded-tr-xs shadow-[0_4px_24px_rgba(0,229,255,0.22)]'
                      : 'bg-[#0B101D]/90 backdrop-blur-xl border border-white/[0.08] text-slate-200 rounded-2xl rounded-tl-xs shadow-[0_4px_24px_rgba(0,0,0,0.4)]'
                  }`}
                >
                  {isUser ? (
                    <p className="leading-relaxed text-sm whitespace-pre-wrap">{msg.content}</p>
                  ) : (
                    <div>{renderFormattedContent(msg.content)}</div>
                  )}

                  {/* Render Visualizations if available */}
                  {msg.chart_data && (
                    <div className="mt-4">
                      <ChartRenderer chartData={msg.chart_data} height={260} />
                    </div>
                  )}

                  {/* Render Tabular Data if available */}
                  {msg.table_data && msg.table_data.length > 0 && (
                    <div className="mt-4">
                      <div className="text-xs font-semibold text-slate-400 mb-1 flex items-center gap-1.5">
                        <TableIcon size={14} className="text-cyan" />
                        <span>Query Result Dataset</span>
                      </div>
                      <DataTable data={msg.table_data} pageSize={5} />
                    </div>
                  )}

                  {/* Render SQL and Execution Metadata */}
                  {msg.metadata?.sql_query && (
                    <div className="mt-3">
                      <SQLViewer
                        sql={msg.metadata.sql_query}
                        executionTimeMs={msg.metadata.execution_time_ms}
                        rowCount={msg.metadata.row_count}
                        dataSources={msg.metadata.data_sources}
                        defaultOpen={false}
                      />
                    </div>
                  )}

                  {/* Render Citations if available */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-4 pt-3.5 border-t border-white/[0.08]">
                      <div className="flex items-center gap-1.5 text-xs text-cyan font-semibold mb-2">
                        <BookOpen size={14} />
                        <span>Verified Citations & Document Sources ({msg.citations.length})</span>
                      </div>
                      <div className="flex flex-col gap-2">
                        {msg.citations.map((c, cIdx) => (
                          <div
                            key={cIdx}
                            className="bg-white/[0.02] border border-white/[0.08] rounded-xl py-2.5 px-3.5 text-xs"
                          >
                            <div className="flex items-center justify-between text-white font-semibold">
                              <span>{c.reference}</span>
                              <span className="text-[10px] text-cyan uppercase font-mono px-2 py-0.5 rounded bg-cyan/10 border border-cyan/20">
                                {c.source_type}
                              </span>
                            </div>
                            {c.excerpt && (
                              <p className="text-slate-400 mt-1.5 text-xs italic leading-relaxed">
                                "{c.excerpt}"
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Timestamp */}
                <span
                  className={`text-[11px] text-slate-500 font-mono px-2 ${
                    isUser ? 'self-end' : 'self-start'
                  }`}
                >
                  {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </div>
          );
        })}

        {/* Loading / Execution indicator */}
        {isLoading && (
          <div className="flex gap-3.5 items-start animate-fade-in">
            <div className="w-9 h-9 rounded-xl bg-[#0E1424] border border-cyan/40 text-cyan flex items-center justify-center shadow-[0_0_12px_rgba(0,229,255,0.2)]">
              <Bot size={17} />
            </div>

            <div className="p-4 px-5 rounded-2xl rounded-tl-xs bg-[#0E1424] border border-cyan/30 text-cyan flex items-center gap-3 shadow-[0_0_20px_rgba(0,229,255,0.12)]">
              <div className="w-4 h-4 border-2 border-cyan/30 border-t-cyan rounded-full animate-spin" />
              <span className="text-xs font-semibold tracking-wide">
                {activeStep || 'Agent is analyzing query context...'}
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* ── Chat Input Bar ───────────────────────────────────────────── */}
      <div className="bg-[#0A0E1A]/95 backdrop-blur-2xl border border-white/10 rounded-2xl py-2 px-3.5 flex items-center gap-3 focus-within:border-cyan/50 focus-within:shadow-[0_0_25px_rgba(0,229,255,0.18)] transition-all shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSendMessage();
            }
          }}
          placeholder="Ask any business question (e.g. 'What were our top products last month?')..."
          disabled={isLoading}
          className="flex-1 bg-transparent border-none outline-none text-white placeholder:text-slate-500 text-sm py-2 px-1 font-medium"
        />

        <button
          onClick={() => handleSendMessage()}
          disabled={!input.trim() || isLoading}
          aria-label="Send message"
          className={`w-10 h-10 rounded-xl border-none flex items-center justify-center transition-all duration-150 shrink-0 ${
            input.trim() && !isLoading
              ? 'bg-gradient-to-r from-cyan via-[#00E5FF] to-violet text-black font-bold cursor-pointer shadow-[0_0_16px_rgba(0,229,255,0.35)] hover:shadow-[0_0_25px_rgba(0,229,255,0.5)] hover:scale-105 active:scale-95'
              : 'bg-white/[0.04] text-slate-600 cursor-not-allowed'
          }`}
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
};

export default AIChatPage;
