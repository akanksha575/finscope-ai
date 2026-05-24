/**
 * Main App Component - Phase 9 React Frontend
 * Three-panel layout with chat, history, and activity/sources
 */
import { useEffect, useState } from 'react';
import Layout from './components/Layout/Layout';
import { useResearch } from './hooks/useResearch';
import './App.css';

function App() {
  const {
    currentQuery,
    plan,
    selectedQuestions,
    isResearching,
    currentReport,
    progressUpdates,
    progress,
    status,
    history,
    conversationHistory,
    currentConversationId,
    error,
    researchDuration,
    researchStartTime,
    handleQuerySubmit,
    handleStartResearch,
    handleSelectReport,
    setSelectedQuestions,
    reset,
    startNewResearch,
    loadHistory,
    clearHistory,
    deleteHistoryItem,
    deleteConversation,
    restoreConversation,
    setCurrentReport: _setCurrentReport,
  } = useResearch();

  const [showError, setShowError] = useState(false);

  // Show error when it's set
  useEffect(() => {
    if (error) {
      setShowError(true);
      // Auto-hide after 5 seconds
      const timer = setTimeout(() => {
        setShowError(false);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  // Note: History is loaded from API via useResearch hook's loadHistory
  // localStorage is managed directly in useResearch hook

  return (
    <div className="h-screen w-screen overflow-hidden bg-fs-black">
      <Layout
        history={history}
        onHistorySelect={(report) => handleSelectReport(report.query_id)}
        selectedReport={currentReport}
        progressUpdates={progressUpdates}
        currentStatus={status}
        plan={plan}
        selectedQuestions={selectedQuestions}
        isResearching={isResearching}
        progress={progress}
        researchDuration={researchDuration}
        researchStartTime={researchStartTime}
        currentQuery={currentQuery}
        conversationHistory={conversationHistory}
        currentConversationId={currentConversationId}
        onQuerySubmit={handleQuerySubmit}
        onQuestionsChange={setSelectedQuestions}
        onStartResearch={handleStartResearch}
        onReset={reset}
        onNewResearch={startNewResearch}
        onRefreshHistory={() => loadHistory(true)}
        onClearHistory={clearHistory}
        onDeleteHistoryItem={deleteHistoryItem}
        onDeleteConversation={deleteConversation}
        onRestoreConversation={restoreConversation}
      />
      
      {/* Error Toast */}
      {error && showError && (
        <div className="fixed bottom-4 right-4 bg-red-950 border border-red-800 text-red-100 px-6 py-3 rounded-lg shadow-card z-50 flex items-center gap-2 max-w-md">
          <span>{error}</span>
          <button
            onClick={() => {
              setShowError(false);
            }}
            className="ml-4 hover:bg-red-900 rounded px-2"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
