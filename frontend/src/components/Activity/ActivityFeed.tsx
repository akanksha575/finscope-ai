/**
 * Activity Feed Component - Real-time updates from research process
 */
import { format } from 'date-fns';
import { 
  Search, 
  DollarSign, 
  Globe, 
  CheckCircle2, 
  XCircle, 
  Loader2,
  ExternalLink 
} from 'lucide-react';
import type { ProgressUpdate } from '../../types/research';

interface ActivityFeedProps {
  updates: ProgressUpdate[];
}

export default function ActivityFeed({ updates }: ActivityFeedProps) {
  const getIcon = (type: string) => {
    switch (type) {
      case 'tool_start':
      case 'tool_complete':
        return <Loader2 className="w-4 h-4 text-zinc-400 animate-spin" />;
      case 'url_accessed':
        return <ExternalLink className="w-4 h-4 text-emerald-400" />;
      case 'data_received':
        return <DollarSign className="w-4 h-4 text-zinc-300" />;
      case 'tool_error':
        return <XCircle className="w-4 h-4 text-red-400" />;
      default:
        return <CheckCircle2 className="w-4 h-4 text-zinc-500" />;
    }
  };

  const getToolIcon = (tool?: string) => {
    switch (tool) {
      case 'web_search':
        return <Search className="w-4 h-4 text-zinc-300" />;
      case 'financial_data':
        return <DollarSign className="w-4 h-4 text-emerald-400" />;
      default:
        return <Globe className="w-4 h-4 text-zinc-500" />;
    }
  };

  if (updates.length === 0) {
    return (
      <div className="p-8 text-center text-zinc-500">
        <Loader2 className="w-12 h-12 mx-auto mb-3 text-zinc-600 animate-spin" />
        <p>No activity yet</p>
        <p className="text-sm mt-1 text-zinc-600">Activity updates will appear here</p>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-3">
      {updates.map((update, index) => (
        <div
          key={index}
          className="bg-fs-card rounded-xl p-3 border border-fs-border hover:bg-fs-elevated transition-colors"
        >
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex-shrink-0">
              {update.tool ? getToolIcon(update.tool) : getIcon(update.type)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-fs-text font-medium break-words">{update.message}</p>
              {update.timestamp && (
                <p className="text-xs text-zinc-600 mt-1">
                  {format(new Date(update.timestamp), 'HH:mm:ss')}
                </p>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
