/**
 * Right Panel - Activity Feed and Sources
 */
import { Activity, FileText, X, Menu } from 'lucide-react';
import ActivityFeed from '../Activity/ActivityFeed';
import SourcesList from '../Sources/SourcesList';
import type { ProgressUpdate } from '../../types/research';
import type { Citation } from '../../types/research';

interface RightPanelProps {
  activeTab: 'activity' | 'sources';
  onTabChange: (tab: 'activity' | 'sources') => void;
  progressUpdates: ProgressUpdate[];
  citations: Citation[];
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export default function RightPanel({
  activeTab,
  onTabChange,
  progressUpdates,
  citations,
  collapsed = false,
  onToggleCollapse,
}: RightPanelProps) {
    if (collapsed) {
      return (
        <div className="w-12 h-full bg-fs-panel flex flex-col border border-fs-border rounded-xl shadow-card flex-shrink-0 overflow-hidden">
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
    <div className="w-80 h-full bg-fs-panel border border-fs-border flex flex-col relative rounded-xl shadow-card flex-shrink-0 overflow-hidden">
      {/* Tab Header */}
      <div className="flex items-center border-b border-fs-border bg-fs-card relative">
        <button
          onClick={() => onTabChange('activity')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors relative border-r border-fs-border ${
            activeTab === 'activity'
              ? 'bg-fs-dark text-fs-highlight border-b-2 border-b-zinc-300'
              : 'text-zinc-500 hover:text-zinc-300 hover:bg-fs-elevated'
          }`}
        >
          <div className="flex items-center justify-center gap-2">
            <Activity className="w-4 h-4" />
            Activity
          </div>
        </button>
        <button
          onClick={() => onTabChange('sources')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors relative ${
            activeTab === 'sources'
              ? 'bg-fs-dark text-fs-highlight border-b-2 border-b-zinc-300'
              : 'text-zinc-500 hover:text-zinc-300 hover:bg-fs-elevated'
          }`}
        >
          <div className="flex items-center justify-center gap-2">
            <FileText className="w-4 h-4" />
            Sources ({citations.length})
          </div>
        </button>
        {onToggleCollapse && (
          <button
            onClick={onToggleCollapse}
            className="px-3 py-3 hover:bg-fs-elevated transition-colors flex items-center justify-center"
            title="Close panel"
          >
            <X className="w-5 h-5 text-fs-muted" />
          </button>
        )}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto bg-fs-dark">
        {activeTab === 'activity' ? (
          <ActivityFeed updates={progressUpdates} />
        ) : (
          <SourcesList citations={citations} />
        )}
      </div>
    </div>
  );
}
