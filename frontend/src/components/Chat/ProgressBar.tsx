/**
 * Progress Bar Component - Real-time progress visualization
 */
import { useState, useEffect } from 'react';
import { CheckCircle2, Loader2, AlertCircle, Clock } from 'lucide-react';
import type { ResearchStatus } from '../../types/research';

interface ProgressBarProps {
  progress: number;
  status: ResearchStatus | string;
  message?: string;
  duration?: number | null;
  startTime?: Date | null;
}

export default function ProgressBar({ progress, status, message, duration, startTime }: ProgressBarProps) {
  const [elapsedTime, setElapsedTime] = useState<number>(0);

  useEffect(() => {
    if (startTime && (status === 'planning' || status === 'researching' || status === 'synthesizing')) {
      const interval = setInterval(() => {
        const elapsed = (new Date().getTime() - startTime.getTime()) / 1000;
        setElapsedTime(elapsed);
      }, 1000);
      return () => clearInterval(interval);
    } else if (duration !== null && duration !== undefined) {
      setElapsedTime(duration);
    }
  }, [startTime, duration, status]);

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    } else if (seconds < 3600) {
      const mins = Math.floor(seconds / 60);
      const secs = Math.round(seconds % 60);
      return `${mins}m ${secs}s`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const mins = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${mins}m`;
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-400" />;
      default:
        return <Loader2 className="w-5 h-5 text-zinc-300 animate-spin" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return 'bg-emerald-500';
      case 'failed':
        return 'bg-red-500';
      default:
        return 'bg-zinc-400';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'planning':
        return 'Planning research queries...';
      case 'researching':
        return 'Executing research queries...';
      case 'synthesizing':
        return 'Synthesizing final report...';
      case 'completed':
        return 'Research completed!';
      case 'failed':
        return 'Research failed';
      default:
        return message || 'Processing...';
    }
  };

  const isStepActive = (step: string) => {
    const order = ['planning', 'researching', 'synthesizing', 'completed'];
    const currentIdx = order.indexOf(status as string);
    const stepIdx = order.indexOf(step);
    return stepIdx <= currentIdx && currentIdx >= 0;
  };

  return (
    <div className="bg-fs-card rounded-2xl border border-fs-border shadow-card p-6">
      <div className="flex items-center gap-3 mb-4">
        {getStatusIcon()}
        <div className="flex-1">
          <h3 className="text-sm font-medium text-fs-highlight">{getStatusText()}</h3>
          <p className="text-xs text-zinc-500 mt-0.5">
            {status !== 'completed' && status !== 'failed' && 'This may take a few minutes'}
          </p>
        </div>
        <span className="text-sm font-medium text-zinc-300">
          {Math.round(progress * 100)}%
        </span>
      </div>

      <div className="w-full bg-fs-elevated rounded-full h-2.5 overflow-hidden">
        <div
          className={`h-full ${getStatusColor()} transition-all duration-300 ease-out`}
          style={{ width: `${progress * 100}%` }}
        />
      </div>

      <div className="flex items-center justify-between mt-4 text-xs text-zinc-500">
        <span className={isStepActive('planning') ? 'text-zinc-200 font-medium' : ''}>Planning</span>
        <span className={isStepActive('researching') ? 'text-zinc-200 font-medium' : ''}>Researching</span>
        <span className={isStepActive('synthesizing') ? 'text-zinc-200 font-medium' : ''}>Synthesizing</span>
        <span className={status === 'completed' ? 'text-emerald-400 font-medium' : ''}>Complete</span>
      </div>

      {(elapsedTime > 0 || duration !== null) && (
        <div className="mt-4 pt-4 border-t border-fs-border flex items-center justify-center gap-2 text-sm text-zinc-400">
          <Clock className="w-4 h-4" />
          <span>
            {status === 'completed' ? 'Completed in' : 'Elapsed time'}:{' '}
            <span className="font-medium text-zinc-200">{formatDuration(elapsedTime)}</span>
          </span>
        </div>
      )}
    </div>
  );
}
