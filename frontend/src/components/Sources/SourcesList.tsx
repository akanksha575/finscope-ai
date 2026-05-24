/**
 * Sources List Component - Displays citations and sources
 */
import { FileText } from 'lucide-react';
import SourceItem from './SourceItem';
import type { Citation } from '../../types/research';

interface SourcesListProps {
  citations: Citation[];
}

export default function SourcesList({ citations }: SourcesListProps) {
  if (citations.length === 0) {
    return (
      <div className="p-8 text-center text-zinc-500">
        <FileText className="w-12 h-12 mx-auto mb-3 text-zinc-600" />
        <p>No sources available</p>
        <p className="text-sm mt-1 text-zinc-600">Sources will appear here after research completes</p>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      <div className="bg-fs-card rounded-xl p-4 border border-fs-border">
        <h3 className="text-sm font-semibold text-fs-highlight mb-2">Sources Summary</h3>
        <div className="text-sm text-zinc-400">
          <span className="font-medium text-zinc-300">{citations.length} Total Sources</span>
        </div>
      </div>

      <div className="space-y-2">
        {citations.map((citation, index) => (
          <SourceItem key={index} citation={citation} />
        ))}
      </div>
    </div>
  );
}
