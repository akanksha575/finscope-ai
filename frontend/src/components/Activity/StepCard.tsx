/**
 * Step Card Component - Individual research step display
 */
import { CheckCircle2, Clock, XCircle } from 'lucide-react';

interface StepCardProps {
  stepNumber: number;
  action: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  finding?: string;
}

export default function StepCard({ stepNumber, action, status, finding }: StepCardProps) {
  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-400" />;
      case 'in_progress':
        return <Clock className="w-5 h-5 text-zinc-300 animate-pulse" />;
      default:
        return <Clock className="w-5 h-5 text-zinc-600" />;
    }
  };

  return (
    <div className="bg-fs-card rounded-xl border border-fs-border p-4">
      <div className="flex items-start gap-3">
        {getStatusIcon()}
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium text-fs-highlight">Step {stepNumber}</span>
            <span className={`px-2 py-0.5 rounded text-xs ${
              status === 'completed' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' :
              status === 'failed' ? 'bg-red-950 text-red-300 border border-red-800' :
              status === 'in_progress' ? 'bg-fs-elevated text-zinc-200 border border-fs-border' :
              'bg-fs-elevated text-zinc-500 border border-fs-border'
            }`}>
              {status.replace('_', ' ')}
            </span>
          </div>
          <p className="text-sm text-zinc-400">{action}</p>
          {finding && (
            <p className="text-xs text-zinc-500 mt-2 italic">{finding}</p>
          )}
        </div>
      </div>
    </div>
  );
}
