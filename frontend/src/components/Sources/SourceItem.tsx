/**
 * Source Item Component - Individual citation display
 */
import { ExternalLink, Calendar } from 'lucide-react';
import type { Citation } from '../../types/research';

interface SourceItemProps {
  citation: Citation;
}

export default function SourceItem({ citation }: SourceItemProps) {
  const handleClick = () => {
    if (citation.url) {
      window.open(citation.url, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <div 
      onClick={handleClick}
      className={`bg-fs-card rounded-xl p-3 border border-fs-border transition-colors ${
        citation.url ? 'hover:bg-fs-elevated cursor-pointer' : ''
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-start gap-2">
            <h4 className="text-sm font-medium text-fs-text mb-1 line-clamp-2 flex-1">
              {citation.title}
            </h4>
            {citation.url && (
              <ExternalLink className="w-4 h-4 text-zinc-500 flex-shrink-0 mt-0.5" />
            )}
          </div>
          <div className="flex items-center gap-2 text-xs text-zinc-500 mb-2">
            <span className="truncate">{citation.domain}</span>
            {citation.published_date && (
              <>
                <span>•</span>
                <div className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  <span>{citation.published_date}</span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
