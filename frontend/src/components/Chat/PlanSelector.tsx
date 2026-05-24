/**
 * Plan Selector Component - UI for displaying research plan and questions
 */
import { Clock } from 'lucide-react';
import type { Plan } from '../../types/plan';

interface PlanSelectorProps {
  plan: Plan;
  selectedQuestions: string[];
  onQuestionsChange: (questions: string[]) => void;
  onStartResearch: () => void;
}

export default function PlanSelector({
  plan,
  selectedQuestions: _selectedQuestions,
  onQuestionsChange: _onQuestionsChange,
  onStartResearch: _onStartResearch,
}: PlanSelectorProps) {
  return (
    <div className="bg-fs-card rounded-2xl border border-fs-border shadow-card p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-fs-highlight mb-1">Deep Research Plan</h3>
        <div className="flex items-center gap-4 text-sm text-zinc-500">
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            <span>{plan.estimated_time}</span>
          </div>
          <span>{plan.steps} research steps</span>
        </div>
        {plan.description && (
          <p className="text-sm text-zinc-400 mt-2">{plan.description}</p>
        )}
      </div>

      <div>
        <h4 className="text-sm font-medium text-zinc-300 mb-3">
          Please provide the following information:
        </h4>
        <div className="space-y-2">
          {plan.questions.map((question, index) => (
            <div key={index} className="text-sm text-zinc-400">
              • {question}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
