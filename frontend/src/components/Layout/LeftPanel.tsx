/**
 * Left Panel - History of previous research queries
 */
import { format } from 'date-fns';
import { History, Search, Menu, RefreshCw, Trash2, X } from 'lucide-react';
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
  onRefresh, 
  onClearHistory, 
  onDeleteItem,
  onDeleteConversation,
  onNewResearch 
}: LeftPanelProps) {
  if (collapsed) {
    return (
      <div className="w-12 bg-fs-panel flex flex-col border-r border-fs-border">
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
    <div className="w-64 bg-fs-panel flex flex-col relative border-r border-fs-border">
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
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-fs-muted" />
          <input
            type="text"
            placeholder="Search history..."
            className="w-full pl-9 pr-3 py-2 bg-fs-card border border-fs-border rounded-lg text-sm text-fs-text placeholder-zinc-500 focus:outline-none focus:border-zinc-500 focus:ring-1 focus:ring-zinc-500 transition-colors"
          />
        </div>
        <div className="flex gap-2">
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-fs-card hover:bg-fs-elevated border border-fs-border rounded-lg text-sm text-fs-text transition-colors"
              title="Refresh history"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Refresh</span>
            </button>
          )}
          {onClearHistory && history && history.length > 0 && (
            <button
              onClick={() => {
                if (window.confirm('Are you sure you want to clear all history? This action cannot be undone.')) {
                  onClearHistory();
                }
              }}
              className="flex items-center justify-center gap-2 px-3 py-2 bg-red-900 hover:bg-red-800 border border-red-800 rounded-lg text-sm text-red-200 transition-colors"
              title="Clear history"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* History List */}
      <div className="flex-1 overflow-y-auto px-2 py-2">
        {(!history || !Array.isArray(history) || history.length === 0) && 
         (!conversationHistory || !Array.isArray(conversationHistory) || conversationHistory.length === 0) ? (
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
                  const isSelected = currentConversationId === conv.id || 
                    (conv.report && selectedReport?.query_id === conv.report.query_id);
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
                                  <span className="px-1.5 py-0.5 rounded bg-fs-elevated text-zinc-300 border border-fs-border">
                                    {conv.sector}
                                  </span>
                                </>
                              )}
                              {conv.status && (
                                <>
                                  <span>•</span>
                                  <span className={`px-1.5 py-0.5 rounded text-xs ${
                                    conv.status === 'completed' ? 'bg-green-900 text-green-300' :
                                    conv.status === 'researching' ? 'bg-blue-900 text-blue-300' :
                                    'bg-fs-elevated text-zinc-400'
                                  }`}>
                                    {conv.status}
                                  </span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                      </button>
                      {(onDeleteItem || onDeleteConversation) && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            const confirmMessage = conv.report 
                              ? 'Are you sure you want to delete this report? This action cannot be undone.'
                              : 'Are you sure you want to delete this conversation? This action cannot be undone.';
                            
                            if (window.confirm(confirmMessage)) {
                              if (conv.report?.query_id && onDeleteItem) {
                                onDeleteItem(conv.report.query_id);
                              } else if (onDeleteConversation) {
                                onDeleteConversation(conv.id);
                              }
                            }
                          }}
                          className="absolute top-2 right-2 p-1.5 opacity-0 group-hover/item:opacity-100 hover:bg-red-900 rounded transition-all"
                          title={conv.report ? "Delete report" : "Delete conversation"}
                        >
                          <Trash2 className="w-3.5 h-3.5 text-red-400" />
                        </button>
                      )}
                    </div>
                  );
                })}
              </>
            )}
            
            {/* Show completed reports from API (that aren't already in conversation history) */}
            {history && Array.isArray(history) && history.length > 0 && (
              <>
                {history
                  .filter(report => {
                    // Only show reports that aren't already represented in conversation history
                    return !conversationHistory?.some(conv => conv.report?.query_id === report.query_id);
                  })
                  .map((report) => (
                    <div
                      key={report.query_id}
                      className={`relative group/item w-full px-3 py-2.5 rounded-lg transition-colors ${
                        selectedReport?.query_id === report.query_id
                          ? 'bg-fs-elevated text-fs-highlight border border-fs-border'
                          : 'text-zinc-300 hover:bg-fs-elevated hover:text-fs-highlight'
                      }`}
                    >
                      <button
                        onClick={() => onSelect(report)}
                        className="w-full text-left"
                      >
                        <div className="flex items-start gap-2">
                          <History className="w-4 h-4 mt-0.5 flex-shrink-0 text-zinc-500 group-hover/item:text-zinc-300" />
                          <div className="flex-1 min-w-0">
                            <h3 className="font-medium text-sm line-clamp-2 mb-1">
                              {report.report.title || report.query}
                            </h3>
                            <div className="flex items-center gap-2 text-xs text-zinc-500">
                              <span>{format(new Date(report.created_at), 'MMM d')}</span>
                              {report.sector && (
                                <>
                                  <span>•</span>
                                  <span className="px-1.5 py-0.5 rounded bg-fs-elevated text-zinc-300 border border-fs-border">
                                    {report.sector}
                                  </span>
                                </>
                              )}
                              {report.status && (
                                <>
                                  <span>•</span>
                                  <span className={`px-1.5 py-0.5 rounded text-xs ${
                                    report.status === 'completed' ? 'bg-green-900 text-green-300' :
                                    report.status === 'researching' ? 'bg-blue-900 text-blue-300' :
                                    report.status === 'pending' ? 'bg-yellow-900 text-yellow-300' :
                                    'bg-fs-elevated text-zinc-400'
                                  }`}>
                                    {report.status}
                                  </span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                      </button>
                      {onDeleteItem && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (window.confirm('Are you sure you want to delete this report? This action cannot be undone.')) {
                              onDeleteItem(report.query_id);
                            }
                          }}
                          className="absolute top-2 right-2 p-1.5 opacity-0 group-hover/item:opacity-100 hover:bg-red-900 rounded transition-all"
                          title="Delete report"
                        >
                          <Trash2 className="w-3.5 h-3.5 text-red-400" />
                        </button>
                      )}
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

