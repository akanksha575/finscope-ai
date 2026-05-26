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
    <div className="bg-white rounded-2xl border border-zinc-200 shadow-sm p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-black mb-1">Deep Research Plan</h3>
        <div className="flex items-center gap-4 text-sm text-black">
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            <span>{plan.estimated_time}</span>
          </div>
          <span>{plan.steps} research steps</span>
        </div>
        {plan.description && (
          <p className="text-sm text-black mt-2">{plan.description}</p>
        )}
      </div>

      <div>
        <h4 className="text-sm font-medium text-black mb-3">
          Please provide the following information:
        </h4>
        <div className="space-y-2">
          {plan.questions.map((question, index) => (
            <div key={index} className="text-sm text-black">
              • {question}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
