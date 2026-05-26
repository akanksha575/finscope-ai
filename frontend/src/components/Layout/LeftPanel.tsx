/**
 * Left Panel - History of previous research queries
 */
import { format } from 'date-fns';

import { History, Search, Menu, X } from 'lucide-react';
// import logo from '../../assets/finscope.png'; // Unused import
import type { ReportResponse } from '../../types/report';

interface ConversationItem {
  id: string;
  query: string;
  sector: string | null;
  plan: any;
  selectedQuestions: string[];
  report: ReportResponse | null;
  progressUpdates: any[];
  researchStartTime: Date | null;
  researchDuration: number | null;
  status: string;
  createdAt: Date;
}

interface LeftPanelProps {
  history: ReportResponse[];
  conversationHistory?: ConversationItem[];
  onSelect: (report: ReportResponse) => void;
  onSelectConversation?: (conversationId: string) => void;
  selectedReport: ReportResponse | null;
  currentConversationId?: string | null;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  onRefresh?: () => void;
  onClearHistory?: () => void;
  onDeleteItem?: (queryId: string) => void;
  onDeleteConversation?: (conversationId: string) => void;
  onNewResearch?: () => void;
}

export default function LeftPanel({ 
  history, 
  conversationHistory = [],
  onSelect, 
  onSelectConversation,
  selectedReport, 
  currentConversationId,
  collapsed = false, 
  onToggleCollapse, 
  onNewResearch 
}: LeftPanelProps) {
    if (collapsed) {
      return (
        <div className="w-12 h-full bg-fs-panel flex flex-col border border-fs-border rounded-xl shadow-card z-10 overflow-hidden flex-shrink-0">
          <button
            onClick={onToggleCollapse}
            className="p-3 hover:bg-fs-elevated transition-colors"
            title="Expand sidebar"
          >
            <Menu className="w-5 h-5 text-fs-muted" />
          </button>
        </div>
      );
    }

    return (
      <div className="w-80 h-full bg-fs-panel flex flex-col relative border border-fs-border rounded-xl shadow-card z-10 overflow-hidden flex-shrink-0">
        {/* Header */}
        <div className="p-3 border-b border-fs-border relative flex items-center">
          <div className="w-full flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-zinc-400 to-zinc-600 flex items-center justify-center flex-shrink-0 shadow-glow">
              <span className="text-zinc-900 text-xs font-bold">FS</span>
            </div>
            <span className="text-sm font-semibold text-fs-text tracking-wide">FinScope</span>
          </div>
          {/* X button - top right */}
          {onToggleCollapse && (
            <button
              onClick={onToggleCollapse}
              className="absolute top-1/2 right-3 -translate-y-1/2 p-2 hover:bg-fs-elevated rounded-lg transition-colors"
              title="Collapse sidebar"
            >
              <X className="w-5 h-5 text-fs-muted" />
            </button>
          )}
        </div>
        {/* New Research Button */}
        {onNewResearch && (
          <div className="p-2 border-b border-fs-border">
            <button
              onClick={onNewResearch}
              className="w-full flex items-center justify-center gap-2 px-3 py-2.5 bg-zinc-200 hover:bg-white text-zinc-900 rounded-lg transition-colors text-sm font-medium shadow-glow"
              title="Start new research"
            >
              <span>+</span>
              <span>New Research</span>
            </button>
          </div>
        )}
        {/* Search and Refresh */}
        <div className="p-2 border-b border-fs-border space-y-2">
          <div className="relative flex items-center">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-fs-muted" />
            <input
              type="text"
              placeholder="Search history..."
              className="w-full pl-9 pr-3 py-2 bg-fs-card border border-fs-border rounded-lg text-sm text-fs-text placeholder-zinc-500 focus:outline-none focus:border-zinc-500 focus:ring-1 focus:ring-zinc-500 transition-colors"
            />
          </div>
          <div className="flex gap-2"></div>
        </div>
        {/* History List */}
        <div className="flex-1 overflow-y-auto px-2 py-2">
          {(!history || !Array.isArray(history) || history.length === 0) && (!conversationHistory || !Array.isArray(conversationHistory) || conversationHistory.length === 0) ? (
            <div className="p-8 text-center">
              <History className="w-12 h-12 mx-auto mb-3 text-zinc-600" />
              <p className="text-zinc-400 text-sm">No research history yet</p>
              <p className="text-xs text-zinc-500 mt-1">Start a new query to see it here</p>
            </div>
          ) : (
            <div className="space-y-1">
              {/* Show conversation history items first */}
              {conversationHistory && Array.isArray(conversationHistory) && conversationHistory.length > 0 && (
                <>
                  {conversationHistory.map((conv) => {
                    const isSelected = currentConversationId === conv.id || (conv.report && selectedReport?.query_id === conv.report.query_id);
                    const displayQuery = conv.query || 'Untitled Query';
                    const displayDate = conv.createdAt ? format(new Date(conv.createdAt), 'MMM d') : 'Recent';
                    return (
                      <div
                        key={conv.id}
                        className={`relative group/item w-full px-3 py-2.5 rounded-lg transition-colors ${
                          isSelected
                            ? 'bg-fs-elevated text-fs-highlight border border-fs-border'
                            : 'text-zinc-300 hover:bg-fs-elevated hover:text-fs-highlight'
                        }`}
                      >
                        <button
                          onClick={() => {
                            if (conv.report && onSelect) {
                              onSelect(conv.report);
                            } else if (onSelectConversation) {
                              onSelectConversation(conv.id);
                            }
                          }}
                          className="w-full text-left"
                        >
                          <div className="flex items-start gap-2">
                            <History className="w-4 h-4 mt-0.5 flex-shrink-0 text-zinc-500 group-hover/item:text-zinc-300" />
                            <div className="flex-1 min-w-0">
                              <h3 className="font-medium text-sm line-clamp-2 mb-1">
                                {conv.report?.report?.title || displayQuery}
                              </h3>
                              <div className="flex items-center gap-2 text-xs text-zinc-500">
                                <span>{displayDate}</span>
                                {conv.sector && (
                                  <>
                                    <span>•</span>
                                    <span className={`px-1.5 py-0.5 rounded ${conv.sector === 'IT' ? 'bg-teal-900 text-teal-200' : conv.sector === 'Pharma' ? 'bg-purple-900 text-purple-200' : 'bg-fs-elevated text-zinc-300'} border border-fs-border`}> {conv.sector}</span>
                                  </>
                                )}
                                {conv.status && (
                                  <>
                                    <span>•</span>
                                    <span className={`px-1.5 py-0.5 rounded text-xs ${
                                      conv.status === 'completed' ? 'bg-green-900 text-green-300' :
                                      conv.status === 'researching' ? 'bg-blue-900 text-blue-300' :
                                      conv.status === 'failed' ? 'bg-red-900 text-red-300' :
                                      conv.status === 'pending' ? 'bg-yellow-900 text-yellow-300' :
                                      'bg-fs-elevated text-zinc-400'
                                    }`}>{conv.status.charAt(0).toUpperCase() + conv.status.slice(1)}</span>
                                  </>
                                )}
                              </div>
                            </div>
                          </div>
                        </button>
                      </div>
                    );
                  })}
                </>
              )}
              {/* Show completed reports from API (that aren't already in conversation history) */}
              {history && Array.isArray(history) && history.length > 0 && (
                <>
                  {history
                    .filter((report) => !conversationHistory?.some((conv) => conv.report?.query_id === report.query_id))
                    .map((report) => (
                      <div
                        key={report.query_id}
                        className={`relative group/item w-full px-3 py-2.5 rounded-lg transition-colors ${
                          selectedReport?.query_id === report.query_id
                            ? 'bg-fs-elevated text-fs-highlight border border-fs-border'
                            : 'text-zinc-300 hover:bg-fs-elevated hover:text-fs-highlight'
                        }`}
                      >
                        <button onClick={() => onSelect(report)} className="w-full text-left">
                          <div className="flex items-start gap-2">
                            <History className="w-4 h-4 mt-0.5 flex-shrink-0 text-zinc-500 group-hover/item:text-zinc-300" />
                            <div className="flex-1 min-w-0">
                              <h3 className="font-medium text-sm line-clamp-2 mb-1">{report.report.title || report.query}</h3>
                              <div className="flex items-center gap-2 text-xs text-zinc-500">
                                <span>{format(new Date(report.created_at), 'MMM d')}</span>
                                {report.sector && (
                                  <>
                                    <span>•</span>
                                    <span className={`px-1.5 py-0.5 rounded ${report.sector === 'IT' ? 'bg-teal-900 text-teal-200' : report.sector === 'Pharma' ? 'bg-purple-900 text-purple-200' : 'bg-fs-elevated text-zinc-300'} border border-fs-border`}> {report.sector}</span>
                                  </>
                                )}
                                {report.status && (
                                  <>
                                    <span>•</span>
                                    <span className={`px-1.5 py-0.5 rounded text-xs ${
                                      report.status === 'completed' ? 'bg-green-900 text-green-300' :
                                      report.status === 'researching' ? 'bg-blue-900 text-blue-300' :
                                      report.status === 'failed' ? 'bg-red-900 text-red-300' :
                                      report.status === 'pending' ? 'bg-yellow-900 text-yellow-300' :
                                      'bg-fs-elevated text-zinc-400'
                                    }`}>{report.status.charAt(0).toUpperCase() + report.status.slice(1)}</span>
                                  </>
                                )}
                              </div>
                            </div>
                          </div>
                        </button>
                      </div>
                    ))}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    );
}
