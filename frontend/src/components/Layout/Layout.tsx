/**
 * Main three-panel layout component
 * History | Main | Activity/Sources
 */
import { useState } from 'react';
// import { Menu } from 'lucide-react'; // Unused import
import LeftPanel from './LeftPanel';
import MainPanel from './MainPanel';
import RightPanel from './RightPanel';
import type { ReportResponse } from '../../types/report';
import type { ProgressUpdate } from '../../types/research';

interface LayoutProps {
  history: ReportResponse[];
  onHistorySelect: (report: ReportResponse) => void;
  selectedReport: ReportResponse | null;
  progressUpdates: ProgressUpdate[];
  currentStatus: string;
  plan: any;
  selectedQuestions: string[];
  isResearching: boolean;
  progress: number;
  researchDuration?: number | null;
  researchStartTime?: Date | null;
  currentQuery?: string;
  onQuerySubmit: (query: string, sector?: any) => void;
  onQuestionsChange: (questions: string[]) => void;
  onStartResearch: () => void;
  onReset: () => void;
  onRefreshHistory?: () => void;
  onClearHistory?: () => void;
  onDeleteHistoryItem?: (queryId: string) => void;
  onDeleteConversation?: (conversationId: string) => void;
  onNewResearch?: () => void;
  onRestoreConversation?: (conversationId: string) => void;
  conversationHistory?: any[];
  currentConversationId?: string | null;
}

export default function Layout({
  history,
  onHistorySelect,
  selectedReport,
  progressUpdates,
  currentStatus,
  plan,
  selectedQuestions,
  isResearching,
  progress,
  researchDuration,
  researchStartTime,
  currentQuery,
  onQuerySubmit,
  onQuestionsChange,
  onStartResearch,
  onReset,
  onRefreshHistory,
  onClearHistory,
  onDeleteHistoryItem,
  onDeleteConversation,
  onNewResearch,
  onRestoreConversation,
  conversationHistory,
  currentConversationId,
}: LayoutProps) {
  const [activeTab, setActiveTab] = useState<'activity' | 'sources'>('activity');
  const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(false);
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState(false);

  return (
    <div className="flex h-screen bg-white overflow-hidden gap-4 p-4 relative">
      {/* Left Panel - History */}
      <LeftPanel
        history={history}
        conversationHistory={conversationHistory}
        onSelect={(report) => {
          // Convert report to query_id for selection
          onHistorySelect(report);
        }}
        onSelectConversation={(conversationId) => {
          // Restore conversation state
          if (onRestoreConversation) {
            onRestoreConversation(conversationId);
          } else {
            // Fallback: Find conversation and select its report if available
            const conv = conversationHistory?.find(c => c.id === conversationId);
            if (conv?.report) {
              onHistorySelect(conv.report);
            }
          }
        }}
        selectedReport={selectedReport}
        currentConversationId={currentConversationId}
        collapsed={leftPanelCollapsed}
        onToggleCollapse={() => setLeftPanelCollapsed(!leftPanelCollapsed)}
        onRefresh={onRefreshHistory}
        onClearHistory={onClearHistory}
        onDeleteItem={onDeleteHistoryItem}
        onDeleteConversation={onDeleteConversation}
        onNewResearch={onNewResearch}
      />

      {/* Main Panel - Chat & Research */}
      <MainPanel
        selectedReport={selectedReport}
        currentStatus={currentStatus}
        plan={plan}
        selectedQuestions={selectedQuestions}
        isResearching={isResearching}
        progress={progress}
        researchDuration={researchDuration}
        researchStartTime={researchStartTime}
        currentQuery={currentQuery}
        onQuerySubmit={onQuerySubmit}
        onQuestionsChange={onQuestionsChange}
        onStartResearch={onStartResearch}
        onReset={onReset}
        conversationHistory={conversationHistory}
        currentConversationId={currentConversationId}
        leftPanelCollapsed={leftPanelCollapsed}
        rightPanelCollapsed={rightPanelCollapsed}
        onToggleLeftPanel={() => setLeftPanelCollapsed(!leftPanelCollapsed)}
        onToggleRightPanel={() => setRightPanelCollapsed(!rightPanelCollapsed)}
      />

      {/* Right Panel - Activity/Sources */}
      <RightPanel
        activeTab={activeTab}
        onTabChange={setActiveTab}
        progressUpdates={progressUpdates}
        citations={selectedReport?.report.all_citations || selectedReport?.report.citations || []}
        collapsed={rightPanelCollapsed}
        onToggleCollapse={() => setRightPanelCollapsed(!rightPanelCollapsed)}
      />
    </div>
  );
}

