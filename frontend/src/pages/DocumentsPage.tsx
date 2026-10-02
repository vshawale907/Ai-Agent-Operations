/* ============================================================================
   DocumentsPage — RAG Document Management & Semantic Vector Search
   ============================================================================ */

import { useState, useRef, type ChangeEvent, type DragEvent, type FormEvent } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FileText,
  UploadCloud,
  Search,
  Trash2,
  CheckCircle2,
  AlertCircle,
  FileCheck,
  Sparkles,
  Layers,
  Clock,
  RefreshCw,
} from 'lucide-react';
import { documentsApi } from '../services/api';
import type { DocumentItem, DocumentSearchResult } from '../types';

export const DocumentsPage = () => {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<DocumentSearchResult[] | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Load documents
  const { data, isLoading: isDocumentsLoading, isError: isDocumentsError, error: documentsError } = useQuery({
    queryKey: ['documents'],
    queryFn: async () => {
      const res = await documentsApi.list();
      return res.documents;
    },
    staleTime: 30000,
  });

  const documents = data;

  // Upload Mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => documentsApi.upload(file),
    onSuccess: (res) => {
      setUploadSuccess(`Successfully indexed "${res.document.filename}" into ${res.document.chunk_count} vector chunks.`);
      setUploadError(null);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setTimeout(() => setUploadSuccess(null), 5000);
    },
    onError: (err: any) => {
      setUploadError(err.response?.data?.detail || 'Failed to upload and vectorize document.');
      setUploadSuccess(null);
    },
  });

  // Delete Mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => documentsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: (err: any) => {
      setUploadError(err.response?.data?.detail || 'Failed to delete document.');
    },
  });

  // Seed Mutation
  const seedMutation = useMutation({
    mutationFn: () => documentsApi.seed(),
    onSuccess: (res: any) => {
      setUploadSuccess(res.message || 'Indexed standard corporate policy documents.');
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setTimeout(() => setUploadSuccess(null), 5000);
    },
    onError: (err: any) => {
      setUploadError(err.response?.data?.detail || 'Failed to seed documents.');
    },
  });

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      uploadMutation.mutate(file);
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      uploadMutation.mutate(file);
    }
  };

  const handleSearch = async (e: FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim() || isSearching) return;

    setIsSearching(true);
    try {
      const res = await documentsApi.search(searchQuery.trim());
      setSearchResults(res.results);
    } catch (err: any) {
      console.error('Semantic search error:', err);
      setUploadError(err.response?.data?.detail || 'Search failed. Backend may not be available.');
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="page-container">
      {/* ── Section Header ────────────────────────────────────────────── */}
      <div className="section-header">
        <div>
          <div className="flex items-center gap-2 text-cyan font-mono text-[11px] font-semibold tracking-wider uppercase mb-1">
            <span className="w-2 h-2 rounded-full bg-cyan shadow-[0_0_8px_#00E5FF] animate-pulse" />
            Vector Intelligence Core
          </div>
          <h1 className="text-2xl md:text-3xl lg:text-4xl font-extrabold text-white tracking-tight">
            RAG Knowledge Base & Documents
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Upload company policies, strategy plans, and operating procedures for autonomous RAG retrieval
          </p>
        </div>

        <button
          onClick={() => seedMutation.mutate()}
          disabled={seedMutation.isPending}
          className="flex items-center gap-2 bg-[#0E1424] border border-white/10 text-slate-200 h-11 px-4 rounded-xl text-xs font-semibold cursor-pointer transition-all duration-200 hover:border-cyan/40 hover:text-white hover:bg-cyan/[0.05] disabled:opacity-50"
        >
          {seedMutation.isPending ? (
            <RefreshCw size={15} className="animate-spin text-cyan" />
          ) : (
            <Sparkles size={15} className="text-cyan" />
          )}
          <span>{seedMutation.isPending ? 'Seeding...' : 'Seed Standard Policies'}</span>
        </button>
      </div>

      {/* ── Status Notifications ──────────────────────────────────────── */}
      {uploadSuccess && (
        <div className="flex items-center gap-3 bg-emerald-500/10 border border-emerald-500/25 rounded-2xl py-3.5 px-5 text-emerald-400 text-sm shadow-[0_0_20px_rgba(16,185,129,0.1)]">
          <CheckCircle2 size={19} className="shrink-0" />
          <span className="font-medium">{uploadSuccess}</span>
        </div>
      )}

      {uploadError && (
        <div className="flex items-center gap-3 bg-rose-500/10 border border-rose-500/25 rounded-2xl py-3.5 px-5 text-rose-400 text-sm shadow-[0_0_20px_rgba(244,63,94,0.1)]">
          <AlertCircle size={19} className="shrink-0" />
          <span className="font-medium">{uploadError}</span>
        </div>
      )}

      {/* ── Drag & Drop Upload Zone ──────────────────────────────────── */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-3xl py-12 md:py-14 px-8 text-center cursor-pointer transition-all duration-300 relative group overflow-hidden ${
          isDragging
            ? 'border-cyan bg-cyan/10 shadow-[0_0_40px_rgba(0,229,255,0.25)] scale-[1.005]'
            : 'border-white/10 bg-[#0E1424]/90 backdrop-blur-md hover:border-cyan/40 hover:bg-cyan/[0.02]'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.md,.markdown,.docx,.doc"
          onChange={handleFileChange}
          className="hidden"
        />

        <div className="w-14 h-14 rounded-2xl bg-cyan/10 border border-cyan/25 inline-flex items-center justify-center mb-4 text-cyan shadow-[0_0_20px_rgba(0,229,255,0.25)] group-hover:scale-105 transition-transform duration-200">
          <UploadCloud size={28} />
        </div>

        <h3 className="text-base md:text-lg font-bold text-white mb-1.5 tracking-tight">
          {uploadMutation.isPending ? 'Processing & Vectorizing Document...' : 'Drag & drop business document or browse'}
        </h3>
        <p className="text-xs md:text-sm text-slate-400 max-w-xl mx-auto leading-relaxed">
          Supports PDF, TXT, Markdown, and DOCX (Max 15MB) • Automatically chunked and embedded with isolated vectors
        </p>
      </div>

      {/* ── Semantic Vector Search Testing Bar ──────────────────────── */}
      <div className="card-base">
        <div className="flex items-center gap-2 mb-3.5 flex-wrap">
          <Search size={18} className="text-cyan" />
          <h3 className="text-sm md:text-base font-bold text-white">
            Vector Search Inspector
          </h3>
          <span className="text-xs text-slate-400">
            • Test semantic cosine similarity directly across your indexed chunks
          </span>
        </div>

        <form onSubmit={handleSearch} className="flex gap-3">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search company knowledge (e.g. 'refund policy for enterprise licenses' or 'APAC expansion')..."
            className="flex-1 bg-white/[0.03] border border-white/10 rounded-xl h-11 px-4 text-white placeholder:text-slate-500 text-sm outline-none focus:border-cyan/60 focus:bg-white/[0.05] focus:shadow-[0_0_15px_rgba(0,229,255,0.15)] transition-all font-medium"
          />
          <button
            type="submit"
            disabled={isSearching || !searchQuery.trim()}
            className="h-11 px-5 bg-gradient-to-r from-cyan via-[#00E5FF] to-violet text-black border-none rounded-xl text-xs font-bold uppercase tracking-wider cursor-pointer flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_20px_rgba(0,229,255,0.25)] hover:shadow-[0_0_30px_rgba(0,229,255,0.45)] hover:-translate-y-0.5 transition-all shrink-0"
          >
            <Search size={15} />
            <span>{isSearching ? 'Searching...' : 'Search Vectors'}</span>
          </button>
        </form>

        {/* Search Results Display */}
        {searchResults !== null && (
          <div className="mt-5 flex flex-col gap-3">
            <span className="text-xs text-slate-400 font-semibold font-mono">
              Found {searchResults.length} relevant semantic matches:
            </span>

            {searchResults.length === 0 ? (
              <div className="p-4 rounded-xl text-slate-400 text-xs bg-white/[0.02] border border-white/[0.06]">
                No chunks matched query with sufficient cosine relevance.
              </div>
            ) : (
              searchResults.map((res, idx) => (
                <div
                  key={idx}
                  className="bg-white/[0.02] border border-white/[0.08] rounded-xl p-4.5 px-5 hover:border-cyan/30 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2 gap-2 flex-wrap">
                    <span className="text-xs md:text-sm font-semibold text-cyan">
                      {res.citation}
                    </span>
                    <span className="text-[11px] font-mono font-semibold py-1 px-2.5 rounded-full bg-cyan/10 text-cyan border border-cyan/25">
                      Score: {(res.score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <p className="text-xs md:text-sm text-slate-300 leading-relaxed">
                    {res.content}
                  </p>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* ── Uploaded Documents Table ─────────────────────────────────── */}
      <div className="card-base">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-cyan/10 border border-cyan/25 text-cyan">
              <FileCheck size={18} />
            </div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Indexed Business Documents ({documents?.length ?? 0})
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            Isolated to your authenticated company workspace
          </span>
        </div>

        {isDocumentsLoading && !documents ? (
          <div className="flex flex-col items-center justify-center py-16 text-cyan">
            <RefreshCw size={24} className="animate-spin mb-3" />
            <span className="font-semibold text-sm">Loading indexed documents...</span>
          </div>
        ) : isDocumentsError ? (
          <div className="border border-rose-500/25 bg-rose-500/10 text-center py-10 rounded-xl mt-4">
            <h3 className="text-base font-bold text-rose-400 mb-1">Unable to load documents</h3>
            <p className="text-sm text-rose-300/80">{(documentsError as any)?.message || 'Check your connection or API status.'}</p>
          </div>
        ) : documents && documents.length === 0 ? (
          <div className="text-center py-12 text-slate-500 text-xs md:text-sm mt-4 border-2 border-dashed border-white/10 rounded-xl">
            No documents uploaded yet. Drag & drop a policy document or click "Seed Standard Policies".
          </div>
        ) : documents ? (
          <div className="overflow-x-auto rounded-xl border border-white/[0.07]">
            <table className="w-full border-collapse text-left text-sm">
              <thead>
                <tr className="border-b border-white/[0.08] bg-white/[0.03]">
                  <th className="py-3.5 px-5 text-slate-400 font-bold uppercase tracking-wider text-xs whitespace-nowrap">Document Title</th>
                  <th className="py-3.5 px-5 text-slate-400 font-bold uppercase tracking-wider text-xs whitespace-nowrap">Type</th>
                  <th className="py-3.5 px-5 text-slate-400 font-bold uppercase tracking-wider text-xs whitespace-nowrap">Chunks</th>
                  <th className="py-3.5 px-5 text-slate-400 font-bold uppercase tracking-wider text-xs whitespace-nowrap">Size</th>
                  <th className="py-3.5 px-5 text-slate-400 font-bold uppercase tracking-wider text-xs whitespace-nowrap">Status</th>
                  <th className="py-3.5 px-5 text-slate-400 font-bold uppercase tracking-wider text-xs whitespace-nowrap text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc: DocumentItem) => (
                  <tr
                    key={doc.id}
                    className="border-b border-white/[0.04] transition-colors duration-150 hover:bg-white/[0.03]"
                  >
                    <td className="py-4 px-5 text-white font-medium whitespace-nowrap">
                      <div className="flex items-center gap-2.5">
                        <FileText size={17} className="text-cyan shrink-0" />
                        <span className="text-sm font-semibold">{doc.filename}</span>
                      </div>
                    </td>
                    <td className="py-4 px-5 text-slate-300 uppercase font-mono whitespace-nowrap">
                      <span className="text-[11px] bg-white/[0.04] border border-white/10 py-1 px-2.5 rounded-lg font-semibold">
                        {doc.file_type}
                      </span>
                    </td>
                    <td className="py-4 px-5 text-cyan font-mono whitespace-nowrap">
                      <span className="inline-flex items-center gap-1.5 text-xs font-semibold">
                        <Layers size={13} />
                        {doc.chunk_count} chunks
                      </span>
                    </td>
                    <td className="py-4 px-5 text-slate-400 font-mono whitespace-nowrap text-xs">
                      {(doc.file_size / 1024).toFixed(1)} KB
                    </td>
                    <td className="py-4 px-5 whitespace-nowrap">
                      {doc.status === 'ready' && (
                        <span className="inline-flex items-center gap-1.5 text-xs py-1 px-3 rounded-full font-semibold border bg-emerald-500/10 text-emerald-400 border-emerald-500/25">
                          <CheckCircle2 size={13} />
                          Ready
                        </span>
                      )}
                      {doc.status === 'failed' && (
                        <div className="flex flex-col gap-1">
                          <span className="inline-flex items-center gap-1.5 text-xs py-1 px-2.5 rounded-full font-semibold border bg-rose-500/10 text-rose-400 border-rose-500/25 w-fit">
                            <AlertCircle size={13} />
                            Failed
                          </span>
                          <span className="text-[11px] text-rose-300/80">
                            Processing failed. <button onClick={() => deleteMutation.mutate(doc.id)} className="underline text-rose-300 hover:text-rose-100 cursor-pointer font-medium">Delete</button> and try again.
                          </span>
                        </div>
                      )}
                      {doc.status !== 'ready' && doc.status !== 'failed' && (
                        <span className="inline-flex items-center gap-1.5 text-xs py-1 px-3 rounded-full font-semibold border bg-amber-500/10 text-amber-400 border-amber-500/25">
                          <Clock size={13} />
                          {doc.status}
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-5 text-right whitespace-nowrap">
                      <button
                        onClick={() => deleteMutation.mutate(doc.id)}
                        disabled={deleteMutation.isPending}
                        title="Delete document"
                        className="w-8 h-8 rounded-lg inline-flex items-center justify-center text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors cursor-pointer border-none bg-transparent"
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default DocumentsPage;
