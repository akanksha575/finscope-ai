/**
 * Main Panel - Chat interface, query input, plan selection, and report display
 */
import QueryInput from '../Chat/QueryInput';
import PlanSelector from '../Chat/PlanSelector';
import ProgressBar from '../Chat/ProgressBar';
import ReportViewer from '../Chat/ReportViewer';

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

interface MainPanelProps {
  selectedReport: ReportResponse | null;
  currentStatus: string;
  plan: any;
  selectedQuestions: string[];
  isResearching: boolean;
  progress: number;
  researchDuration?: number | null;
  researchStartTime?: Date | null;
  currentQuery?: string;
  conversationHistory?: ConversationItem[];
  currentConversationId?: string | null;
  onQuerySubmit: (query: string, sector?: any) => void;
  onQuestionsChange: (questions: string[]) => void;
  onStartResearch: () => void;
  onReset: () => void;
  leftPanelCollapsed?: boolean;
  rightPanelCollapsed?: boolean;
  onToggleLeftPanel?: () => void;
  onToggleRightPanel?: () => void;
}

export default function MainPanel({
  selectedReport,
  currentStatus,
  plan,
  selectedQuestions,
  isResearching,
  progress,
  researchDuration,
  researchStartTime,
  currentQuery,
  conversationHistory = [],
  currentConversationId,
  onQuerySubmit,
  onQuestionsChange,
  onStartResearch,
  onReset: _onReset,
  leftPanelCollapsed = false,
  rightPanelCollapsed = false,
  onToggleLeftPanel: _onToggleLeftPanel,
  onToggleRightPanel: _onToggleRightPanel,
}: MainPanelProps) {
  return (
    <div className="flex-1 h-full flex flex-col bg-white overflow-hidden relative">

      
      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto pb-32 pt-0 flex flex-col">
        <div className={`w-full mx-auto px-4 py-8 flex-1 flex flex-col ${leftPanelCollapsed && rightPanelCollapsed ? 'max-w-7xl' : leftPanelCollapsed || rightPanelCollapsed ? 'max-w-6xl' : 'max-w-5xl'}`}>
          {/* Display ONLY the current conversation - filter by currentConversationId */}
          {(() => {
            // Filter to show only the current conversation
            const currentConversation = currentConversationId 
              ? conversationHistory.filter(item => item.id === currentConversationId)
              : [];
            
            // If we have a current conversation in history, show it with current state values
            if (currentConversation.length > 0 && (currentQuery || plan || isResearching || selectedReport)) {
              const item = currentConversation[0];
              const isActive = item.id === currentConversationId;
              
              return (
                <div key={item.id} className="space-y-4 pb-8">

                  {/* Plan Selection - use current plan if active, otherwise use item plan */}
                  {(isActive ? plan : item.plan) && (isActive ? !isResearching : item.status !== 'researching') && (
                    <PlanSelector
                      plan={isActive ? plan : item.plan}
                      selectedQuestions={isActive ? selectedQuestions : item.selectedQuestions}
                      onQuestionsChange={isActive ? onQuestionsChange : () => {}}
                      onStartResearch={isActive ? onStartResearch : () => {}}
                    />
                  )}

                  {/* Progress Bar - use current state if active, otherwise use item state */}
                  {((isActive && (isResearching || currentStatus === 'completed' || progress > 0)) || 
                    (!isActive && (item.status === 'researching' || item.status === 'completed'))) && (
                    <ProgressBar
                      progress={isActive ? progress : (item.status === 'completed' ? 1 : 0)}
                      status={isActive ? currentStatus as any : (item.status as any)}
                      message="Research in progress..."
                      duration={isActive ? researchDuration : item.researchDuration}
                      startTime={isActive ? researchStartTime : item.researchStartTime}
                    />
                  )}

                  {/* Report Display - use current report if active, otherwise use item report */}
                  {(isActive ? selectedReport : item.report) && (
                    <div className="mt-4">
                      <ReportViewer report={isActive ? selectedReport! : item.report!} />
                    </div>
                  )}
                </div>
              );
            }
            return null;
          })()}

          {/* Current active query/plan (if not yet in history OR if report exists but not in history) */}
          {/* Only show if there's no current conversation in history yet */}
          {currentConversationId && !conversationHistory.some(item => item.id === currentConversationId) && (
            <div className="space-y-4 pb-8">

              {/* Plan Selection */}
              {plan && !isResearching && (
                <PlanSelector
                  plan={plan}
                  selectedQuestions={selectedQuestions}
                  onQuestionsChange={onQuestionsChange}
                  onStartResearch={onStartResearch}
                />
              )}

              {/* Progress Bar */}
              {(isResearching || currentStatus === 'completed' || progress > 0) && (
                <ProgressBar
                  progress={progress}
                  status={currentStatus as any}
                  message="Research in progress..."
                  duration={researchDuration}
                  startTime={researchStartTime}
                />
              )}

              {/* Report Display - Always show if selectedReport exists */}
              {selectedReport && (
                <div className="mt-4">
                  <ReportViewer report={selectedReport} />
                </div>
              )}
            </div>
          )}
          
          {/* Fallback: Show current state if no conversation ID yet (shouldn't happen, but safety check) */}
          {!currentConversationId && (currentQuery || plan || isResearching || selectedReport) && (
            <div className="space-y-4 pb-8">

              {/* Plan Selection */}
              {plan && !isResearching && (
                <PlanSelector
                  plan={plan}
                  selectedQuestions={selectedQuestions}
                  onQuestionsChange={onQuestionsChange}
                  onStartResearch={onStartResearch}
                />
              )}

              {/* Progress Bar */}
              {(isResearching || currentStatus === 'completed' || progress > 0) && (
                <ProgressBar
                  progress={progress}
                  status={currentStatus as any}
                  message="Research in progress..."
                  duration={researchDuration}
                  startTime={researchStartTime}
                />
              )}

              {/* Report Display - Always show if selectedReport exists */}
              {selectedReport && (
                <div className="mt-4">
                  <ReportViewer report={selectedReport} />
                </div>
              )}
            </div>
          )}

          {/* Welcome screen - show when there's no active query/research, regardless of history */}
          {!currentQuery && !plan && !isResearching && !selectedReport && (
            <div className="flex-1 flex flex-col items-center justify-center min-h-[60vh]">
              <div className="text-center space-y-6 max-w-2xl px-6 mt-[-10vh]">
                <div className="space-y-3">
                  <h1 className="text-4xl font-semibold text-zinc-900 tracking-tight">
                    What would you like to research?
                  </h1>
                  <p className="text-lg text-black">
                    Get comprehensive financial insights powered by AI
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Fixed Input Area at Bottom */}
      <div className="absolute bottom-0 left-0 right-0 bg-fs-dark/95 backdrop-blur-sm border-t border-fs-border">
        <div className={`w-full mx-auto px-4 py-4 ${leftPanelCollapsed && rightPanelCollapsed ? 'max-w-7xl' : leftPanelCollapsed || rightPanelCollapsed ? 'max-w-6xl' : 'max-w-5xl'}`}>
          <QueryInput
            onQuerySubmit={onQuerySubmit}
            disabled={isResearching}
            hasPlan={!!plan && !isResearching}
            onStartResearch={onStartResearch}
          />
        </div>
      </div>
    </div>
  );
}

