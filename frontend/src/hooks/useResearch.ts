/**
 * Custom hook for managing research workflow
 */
import { useState, useCallback, useEffect, useRef } from 'react';
import { classifyQuery, generatePlan, listReports, getReport, deleteReport, deleteAllReports } from '../services/api';
import { researchWebSocket } from '../services/websocket';
import type { 
  Sector, 
  ResearchRequest, 
  ProgressUpdate,
  Plan 
} from '../types';
import type { ReportResponse } from '../types/report';

interface ConversationItem {
  id: string;
  query: string;
  sector: Sector | null;
  plan: Plan | null;
  selectedQuestions: string[];
  report: ReportResponse | null;
  progressUpdates: ProgressUpdate[];
  researchStartTime: Date | null;
  researchDuration: number | null;
  status: string;
  createdAt: Date;
}

export function useResearch() {
  const [currentQuery, setCurrentQuery] = useState<string>('');
  const [sector, setSector] = useState<Sector | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [selectedQuestions, setSelectedQuestions] = useState<string[]>([]);
  const [isResearching, setIsResearching] = useState(false);
  const [currentReport, setCurrentReport] = useState<ReportResponse | null>(null);
  const [progressUpdates, setProgressUpdates] = useState<ProgressUpdate[]>([]);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<string>('idle');
  const [history, setHistory] = useState<ReportResponse[]>([]);
  
  // Load conversationHistory from localStorage on mount
  const [conversationHistory, setConversationHistory] = useState<ConversationItem[]>(() => {
    try {
      const stored = globalThis.localStorage?.getItem('conversation_history');
      if (stored) {
        const parsed = JSON.parse(stored);
        // Convert date strings back to Date objects
        const converted = parsed.map((item: any) => ({
          ...item,
          createdAt: item.createdAt ? new Date(item.createdAt) : new Date(),
          researchStartTime: item.researchStartTime ? new Date(item.researchStartTime) : null,
        }));
        
        // Remove duplicates on load
        const seenIds = new Set<string>();
        const deduplicated = converted.filter((conv: ConversationItem) => {
          if (seenIds.has(conv.id)) {
            console.log('Removing duplicate conversation on load:', conv.id);
            return false;
          }
          seenIds.add(conv.id);
          return true;
        });
        
        return deduplicated;
      }
    } catch (error) {
      console.error('Error loading conversation history from localStorage:', error);
    }
    return [];
  });
  
  // Persist conversationHistory to localStorage whenever it changes
  useEffect(() => {
    try {
      // Deduplicate before saving
      const seenIds = new Set<string>();
      const deduplicated = conversationHistory.filter(conv => {
        if (seenIds.has(conv.id)) {
          console.log('Removing duplicate conversation before saving to localStorage:', conv.id);
          return false;
        }
        seenIds.add(conv.id);
        return true;
      });
      
      if (deduplicated.length > 0 || globalThis.localStorage?.getItem('conversation_history')) {
        globalThis.localStorage.setItem('conversation_history', JSON.stringify(deduplicated));
      }
    } catch (error) {
      console.error('Error saving conversation history to localStorage:', error);
    }
  }, [conversationHistory]);
  
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(() => {
    try {
      return globalThis.localStorage?.getItem('current_conversation_id') || null;
    } catch (error) {
      return null;
    }
  });
  
  // Persist currentConversationId to localStorage
  useEffect(() => {
    try {
      if (currentConversationId) {
        globalThis.localStorage?.setItem('current_conversation_id', currentConversationId);
      } else {
        globalThis.localStorage?.removeItem('current_conversation_id');
      }
    } catch (error) {
      console.error('Error saving current conversation ID to localStorage:', error);
    }
  }, [currentConversationId]);
  const [error, setError] = useState<string | null>(null);
  const [researchStartTime, setResearchStartTime] = useState<Date | null>(null);
  const [researchDuration, setResearchDuration] = useState<number | null>(null);
  const [isHistoryCleared, setIsHistoryCleared] = useState(false);
  const isHistoryClearedRef = useRef(false);

  // Define loadHistory before using it
  const loadHistory = useCallback(async (force = false) => {
    console.log('loadHistory called with force=', force, 'isHistoryCleared=', isHistoryCleared, 'ref=', isHistoryClearedRef.current);
    // Don't load if history was just cleared (unless forced) - check both state and ref
    if ((isHistoryCleared || isHistoryClearedRef.current) && !force) {
      console.log('Skipping loadHistory - history was cleared and not forcing');
      return;
    }
    // Reset flag if forcing reload
    if (force) {
      console.log('Resetting isHistoryCleared flag because force=true');
      setIsHistoryCleared(false);
      isHistoryClearedRef.current = false;
    }
    try {
      console.log('Loading history...');
      const reports = await listReports();
      console.log('History loaded:', reports);
      console.log('Reports type:', typeof reports, 'Is array:', Array.isArray(reports));
      
      // Handle different response formats
      let historyArray: ReportResponse[] = [];
      if (Array.isArray(reports)) {
        historyArray = reports;
      } else if (reports && typeof reports === 'object') {
        // If it's an object, try to extract an array from it
        if ('data' in reports && Array.isArray((reports as any).data)) {
          historyArray = (reports as any).data;
        } else if ('reports' in reports && Array.isArray((reports as any).reports)) {
          historyArray = (reports as any).reports;
        } else {
          // If it's a single report object, wrap it in an array
          historyArray = [reports as any];
        }
      }
      
      console.log('History array after processing:', historyArray.length, 'items');
      // Only update history if not cleared (double-check with ref)
      if (!isHistoryClearedRef.current) {
        setHistory(historyArray);
        
        // Sync conversationHistory with API history - add any reports that aren't in conversationHistory
        setConversationHistory(prev => {
          // First, remove duplicates by ID
          const seenIds = new Set<string>();
          const deduplicated = prev.filter(conv => {
            if (seenIds.has(conv.id)) {
              console.log('Removing duplicate conversation ID in loadHistory:', conv.id);
              return false;
            }
            seenIds.add(conv.id);
            return true;
          });
          
          const updated = [...deduplicated];
          let hasChanges = false;
          
          historyArray.forEach(report => {
            // Check if this report is already in conversationHistory (by query_id OR by ID pattern)
            const existsByQueryId = updated.some(conv => conv.report?.query_id === report.query_id);
            const convIdPattern = `conv-${report.query_id}`;
            const existsById = updated.some(conv => conv.id === convIdPattern);
            
            if (!existsByQueryId && !existsById) {
              // Create a conversation item for this report
              const convId = convIdPattern;
              // Add to beginning of list so it appears at top
              updated.unshift({
                id: convId,
                query: report.query,
                sector: report.sector as Sector,
                plan: null,
                selectedQuestions: [],
                report: report,
                progressUpdates: [],
                researchStartTime: report.created_at ? new Date(report.created_at) : null,
                researchDuration: report.metadata?.duration_seconds || null,
                status: report.status || 'completed', // Use actual status from report
                createdAt: report.created_at ? new Date(report.created_at) : new Date()
              });
              hasChanges = true;
            } else if (existsByQueryId && !existsById) {
              // Update existing conversation to use the standard ID format if needed
              const existingIndex = updated.findIndex(conv => conv.report?.query_id === report.query_id);
              if (existingIndex >= 0 && updated[existingIndex].id !== convIdPattern) {
                updated[existingIndex] = {
                  ...updated[existingIndex],
                  id: convIdPattern, // Standardize ID
                  report: report, // Update report data
                  status: report.status || updated[existingIndex].status
                };
                hasChanges = true;
              }
            }
          });
          
          // Sort by creation date (newest first)
          if (hasChanges) {
            updated.sort((a, b) => {
              const dateA = a.createdAt?.getTime() || 0;
              const dateB = b.createdAt?.getTime() || 0;
              return dateB - dateA;
            });
          }
          
          // Final deduplication pass to ensure no duplicates
          const finalSeenIds = new Set<string>();
          const finalDeduplicated = updated.filter(conv => {
            if (finalSeenIds.has(conv.id)) {
              console.log('Removing duplicate conversation ID in final pass:', conv.id);
              return false;
            }
            finalSeenIds.add(conv.id);
            return true;
          });
          
          return finalDeduplicated;
        });
        
        console.log('History state updated successfully');
      } else {
        console.log('Skipping history update - history was cleared');
      }
    } catch (error: any) {
      console.error('Failed to load history:', error);
      console.error('Error details:', error.response?.data || error.message);
      // On error, ensure history is still an array
      setHistory([]);
    }
  }, [isHistoryCleared]);

  // Load history on mount (only if not cleared)
  useEffect(() => {
    if (!isHistoryCleared) {
      loadHistory().catch(err => {
        console.error('Failed to load history on mount:', err);
        // Don't set error state here - just log it so the app can still render
      });
    }
  }, [loadHistory, isHistoryCleared]);

  // Setup WebSocket listeners - use refs to access latest values
  const researchStartTimeRef = useRef<Date | null>(null);
  researchStartTimeRef.current = researchStartTime;
  const currentConversationIdRef = useRef<string | null>(null);
  currentConversationIdRef.current = currentConversationId;
  const progressUpdatesRef = useRef<ProgressUpdate[]>([]);
  progressUpdatesRef.current = progressUpdates;
  const researchDurationRef = useRef<number | null>(null);
  researchDurationRef.current = researchDuration;
  const sectorRef = useRef<Sector | null>(null);
  sectorRef.current = sector;
  const planRef = useRef<Plan | null>(null);
  planRef.current = plan;
  const selectedQuestionsRef = useRef<string[]>([]);
  selectedQuestionsRef.current = selectedQuestions;

  useEffect(() => {
    const handleMessage = (update: ProgressUpdate) => {
      // Update progress and status in real-time - this should happen immediately
      setProgressUpdates(prev => {
        const updated = [...prev, update];
        progressUpdatesRef.current = updated;
        // Update conversation history with progress updates
        const convId = currentConversationIdRef.current;
        if (convId) {
          setConversationHistory(prevConv => prevConv.map(item => 
            item.id === convId 
              ? { ...item, progressUpdates: updated }
              : item
          ));
        }
        return updated;
      });
      
      if (update.progress !== undefined) {
        setProgress(update.progress);
      }
      
      if (update.status) {
        setStatus(update.status);
      }
      
      // Handle completion
      if (update.type === 'complete' || update.status === 'completed') {
        console.log('Research completed, update:', update);
        setIsResearching(false);
        setStatus('completed');
        setProgress(1);
        
        // Calculate duration using ref to get latest value
        const startTime = researchStartTimeRef.current;
        let calculatedDuration = researchDurationRef.current;
        if (startTime && !calculatedDuration) {
          calculatedDuration = (new Date().getTime() - startTime.getTime()) / 1000; // in seconds
          setResearchDuration(calculatedDuration);
          researchDurationRef.current = calculatedDuration;
        }
        
        // Reload history when research completes
        const completeResearch = async () => {
          // If query_id is provided, fetch and display the report
          const queryId = update.query_id || (update as any).query_id;
          
          // Check if report is already in the update (from WebSocket)
          const reportFromUpdate = (update as any).report;
          if (reportFromUpdate && reportFromUpdate.query_id) {
            console.log('Using report from WebSocket update:', reportFromUpdate.query_id);
            // Use the report directly from WebSocket if it's properly structured
            setCurrentReport(reportFromUpdate);
            setStatus('completed');
            setProgress(1);
            setIsResearching(false);
            
            // Update conversation history
            const convId = currentConversationIdRef.current;
            const latestProgressUpdates = progressUpdatesRef.current;
            const latestDuration = researchDurationRef.current || calculatedDuration;
            
            if (convId) {
              setConversationHistory(prev => {
                const updated = prev.map(item => 
                  item.id === convId 
                    ? { 
                        ...item, 
                        report: reportFromUpdate,
                        progressUpdates: latestProgressUpdates,
                        researchDuration: latestDuration,
                        status: 'completed'
                      }
                    : item
                );
                // Move completed item to top
                const completedIndex = updated.findIndex(item => item.id === convId);
                if (completedIndex > 0) {
                  const completedItem = updated[completedIndex];
                  updated.splice(completedIndex, 1);
                  updated.unshift(completedItem);
                }
                return updated;
              });
            }
            
            // Immediately add to history state (don't wait for API)
            setHistory(prev => {
              // Check if report already exists
              const exists = prev.some(r => r.query_id === reportFromUpdate.query_id);
              if (!exists) {
                return [reportFromUpdate, ...prev];  // Add to beginning
              }
              // Update existing
              return prev.map(r => 
                r.query_id === reportFromUpdate.query_id ? reportFromUpdate : r
              );
            });
            
            // Reload history from API after a short delay to ensure DB is synced
            setTimeout(async () => {
              try {
                await loadHistory(true);
                console.log('History reloaded from API after report completion');
              } catch (err) {
                console.error('Error reloading history:', err);
              }
            }, 500);  // Reduced delay - UI already updated
            return;
          }
          
          if (queryId) {
            console.log('Loading report with query_id:', queryId);
            // Wait a bit for the database to be fully updated
            setTimeout(async () => {
              try {
                const report = await getReport(queryId);
                console.log('Report fetched successfully:', report);
                console.log('Setting currentReport to:', report.query_id);
                
                // Always set currentReport first - this ensures it displays
                setCurrentReport(report);
                setStatus('completed');
                setProgress(1);
                setIsResearching(false);
                
                // Update conversation history with completed report using refs
                const convId = currentConversationIdRef.current;
                const latestProgressUpdates = progressUpdatesRef.current;
                const latestDuration = researchDurationRef.current || calculatedDuration;
                
                console.log('Current conversation ID:', convId);
                console.log('Progress updates count:', latestProgressUpdates.length);
                console.log('Research duration:', latestDuration);
                
                if (convId) {
                  console.log('Updating conversation history with report for conversation:', convId);
                  setConversationHistory(prev => {
                    const updated = prev.map(item => 
                      item.id === convId 
                        ? { 
                            ...item, 
                            report: report,
                            progressUpdates: latestProgressUpdates,
                            researchDuration: latestDuration,
                            status: 'completed'
                          }
                        : item
                    );
                    // Move completed item to top
                    const completedIndex = updated.findIndex(item => item.id === convId);
                    if (completedIndex > 0) {
                      const completedItem = updated[completedIndex];
                      updated.splice(completedIndex, 1);
                      updated.unshift(completedItem);
                    }
                    console.log('Conversation history updated. Last item has report:', updated[updated.length - 1]?.report !== null);
                    return updated;
                  });
                } else {
                  console.warn('No currentConversationId found, creating new conversation item for report');
                  // If no conversation ID, create one now to ensure report is in history
                  // Use refs to get the latest values
                  const fallbackConvId = `conv-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
                  const currentQueryValue = currentQuery || report.query;
                  const currentSector = sectorRef.current;
                  const currentPlan = planRef.current;
                  const currentSelectedQuestions = selectedQuestionsRef.current;
                  const currentResearchStartTime = researchStartTimeRef.current;
                  
                  setConversationHistory(prev => {
                    // Check if this report already exists in history
                    const existingIndex = prev.findIndex(item => item.report?.query_id === report.query_id);
                    if (existingIndex >= 0) {
                      // Update existing and move to top
                      const updated = [...prev];
                      const existingItem = updated[existingIndex];
                      updated.splice(existingIndex, 1);  // Remove from current position
                      updated.unshift({  // Add to beginning
                        ...existingItem,
                        report: report,
                        progressUpdates: latestProgressUpdates,
                        researchDuration: latestDuration,
                        status: 'completed'
                      });
                      return updated;
                    } else {
                      // Add new to beginning
                      return [{
                        id: fallbackConvId,
                        query: currentQueryValue,
                        sector: currentSector,
                        plan: currentPlan,
                        selectedQuestions: currentSelectedQuestions,
                        report: report,
                        progressUpdates: latestProgressUpdates,
                        researchStartTime: currentResearchStartTime,
                        researchDuration: latestDuration,
                        status: 'completed',
                        createdAt: currentResearchStartTime || new Date()
                      }, ...prev];
                    }
                  });
                  // Set the conversation ID so future updates use it
                  setCurrentConversationId(fallbackConvId);
                  currentConversationIdRef.current = fallbackConvId;
                }
                
                // Immediately add to history state
                setHistory(prev => {
                  const exists = prev.some(r => r.query_id === report.query_id);
                  if (!exists) {
                    return [report, ...prev];  // Add to beginning
                  }
                  return prev.map(r => r.query_id === report.query_id ? report : r);
                });
                
                // Reload history from API after a short delay to ensure DB is synced
                setTimeout(async () => {
                  try {
                    await loadHistory(true); // Force reload after new report
                    console.log('History reloaded from API after report completion');
                  } catch (err) {
                    console.error('Error reloading history:', err);
                  }
                }, 500);  // Reduced delay - UI already updated
                console.log('Report loaded successfully');
              } catch (err) {
                console.error('Failed to load report:', err);
                // Fallback: reload history and select latest
                setTimeout(async () => {
                  await loadHistory(true); // Force reload
                  const reports = await listReports();
                  if (reports.length > 0 && Array.isArray(reports)) {
                    try {
                      const report = await getReport(reports[0].query_id);
                      setCurrentReport(report);
                      setStatus('completed');
                      setProgress(1);
                      setIsResearching(false);
                    } catch (reportErr) {
                      console.error('Failed to load latest report:', reportErr);
                    }
                  }
                }, 500);
              }
            }, 1500);
          } else {
            console.log('No query_id in update, using fallback');
                // Fallback: reload history and auto-select the latest report
            setTimeout(async () => {
              try {
                // Reset cleared flag and reload history after new report
                setIsHistoryCleared(false);
                await loadHistory(true); // Force reload after new report
                // Get the updated history after loading
                const reports = await listReports();
                if (reports.length > 0 && Array.isArray(reports)) {
                  const latestReport = reports[0];
                  console.log('Auto-selecting latest report:', latestReport.query_id);
                  try {
                    const report = await getReport(latestReport.query_id);
                    setCurrentReport(report);
                    setStatus('completed');
                    setProgress(1);
                    setIsResearching(false);
                    
                    // Immediately add to history state
                    setHistory(prev => {
                      const exists = prev.some(r => r.query_id === report.query_id);
                      if (!exists) {
                        return [report, ...prev];
                      }
                      return prev.map(r => r.query_id === report.query_id ? report : r);
                    });
                    
                    // Update conversation history with the report
                    setConversationHistory(prev => {
                      const existingIndex = prev.findIndex(item => item.report?.query_id === report.query_id);
                      if (existingIndex >= 0) {
                        const updated = [...prev];
                        updated[existingIndex] = {
                          ...updated[existingIndex],
                          report: report,
                          status: 'completed'
                        };
                        return updated;
                      }
                      return prev;
                    });
                  } catch (err) {
                    console.error('Failed to load latest report:', err);
                  }
                }
              } catch (err) {
                console.error('Error in fallback history reload:', err);
              }
            }, 1000);  // Reduced delay
          }
        };
        
        completeResearch();
      }
    };

    const handleError = (err: any) => {
      console.error('WebSocket error:', err);
      setError('Connection error. Please try again.');
      setIsResearching(false);
    };

    const handleClose = () => {
      console.log('WebSocket closed');
    };

    const handleReconnecting = () => {
      console.log('Reconnecting...');
    };

    researchWebSocket.on('message', handleMessage);
    researchWebSocket.on('error', handleError);
    researchWebSocket.on('close', handleClose);
    researchWebSocket.on('reconnecting', handleReconnecting);

    return () => {
      researchWebSocket.off('message', handleMessage);
      researchWebSocket.off('error', handleError);
      researchWebSocket.off('close', handleClose);
      researchWebSocket.off('reconnecting', handleReconnecting);
    };
  }, []);

  const handleQuerySubmit = useCallback(async (query: string, sector?: Sector) => {
    // Save current conversation item if it exists
    if (currentQuery && currentConversationId) {
      setConversationHistory(prev => prev.map(item => 
        item.id === currentConversationId 
          ? {
              ...item,
              query: currentQuery,
              sector: sector || null,
              plan: plan,
              selectedQuestions: selectedQuestions,
              report: currentReport,
              progressUpdates: progressUpdates,
              researchStartTime: researchStartTime,
              researchDuration: researchDuration,
              status: status
            }
          : item
      ));
    }
    
    // Create new conversation item
    const newConversationId = `conv-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    setCurrentConversationId(newConversationId);
    
    const newConversationItem: ConversationItem = {
      id: newConversationId,
      query: query,
      sector: null,
      plan: null,
      selectedQuestions: [],
      report: null,
      progressUpdates: [],
      researchStartTime: null,
      researchDuration: null,
      status: 'idle',
      createdAt: new Date()
    };
    
    // Add to beginning of list so it appears at top
    setConversationHistory(prev => {
      // Remove any duplicates first
      const seenIds = new Set<string>();
      const deduplicated = prev.filter(conv => {
        if (seenIds.has(conv.id)) {
          console.log('Removing duplicate conversation before adding new:', conv.id);
          return false;
        }
        seenIds.add(conv.id);
        return true;
      });
      
      // Check if conversation already exists (shouldn't happen, but be safe)
      const exists = deduplicated.some(item => item.id === newConversationId);
      if (!exists) {
        console.log('Adding new conversation to history:', newConversationId, newConversationItem.query);
        return [newConversationItem, ...deduplicated];
      } else {
        console.log('Conversation already exists, updating it:', newConversationId);
        // Update existing conversation and move to top
        const updated = deduplicated.map(item => 
          item.id === newConversationId 
            ? { ...item, ...newConversationItem }
            : item
        );
        // Move updated item to top
        const updatedIndex = updated.findIndex(item => item.id === newConversationId);
        if (updatedIndex > 0) {
          const updatedItem = updated[updatedIndex];
          updated.splice(updatedIndex, 1);
          updated.unshift(updatedItem);
        }
        return updated;
      }
    });
    
    setCurrentQuery(query);
    setError(null);
    setProgressUpdates([]);
    setProgress(0);
    
    try {
      // Classify query if sector not provided
      let detectedSector = sector;
      if (!detectedSector) {
        const classification = await classifyQuery({ query });
        detectedSector = classification.sector;
      }
      setSector(detectedSector);
      
      // Generate plan
      const planResponse = await generatePlan({
        query,
        sector: detectedSector,
      });
      setPlan(planResponse.plan);
      setSelectedQuestions([]);
      
      // Update conversation item with sector and plan
      setConversationHistory(prev => {
        const updated = prev.map(item => 
          item.id === newConversationId 
            ? { ...item, sector: detectedSector, plan: planResponse.plan }
            : item
        );
        // Ensure the conversation exists (in case it wasn't created yet)
        const exists = updated.some(item => item.id === newConversationId);
        if (!exists) {
          console.log('Conversation not found, creating it now:', newConversationId);
          return [{
            id: newConversationId,
            query: query,
            sector: detectedSector,
            plan: planResponse.plan,
            selectedQuestions: [],
            report: null,
            progressUpdates: [],
            researchStartTime: null,
            researchDuration: null,
            status: 'idle',
            createdAt: new Date()
          }, ...updated];
        }
        return updated;
      });
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to process query';
      setError(errorMsg);
      console.error('Query submission error:', err);
    }
  }, [currentQuery, currentConversationId, sector, plan, selectedQuestions, currentReport, progressUpdates, researchStartTime, researchDuration, status]);

  const handleStartResearch = useCallback(async () => {
    if (!currentQuery || !sector) {
      setError('Please provide a query first');
      return;
    }
    
    // If no questions are selected but plan exists, mark all questions as selected
    // (user provided information via input field)
    if (plan && selectedQuestions.length === 0) {
      setSelectedQuestions(plan.questions);
    }

      // CRITICAL: Ensure we have a conversation ID before starting research
      // If not, create one now (this can happen if user clicks "New Research" then submits query)
      let convId = currentConversationId;
      if (!convId) {
        convId = `conv-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
        setCurrentConversationId(convId);
        currentConversationIdRef.current = convId;
        
        // Create conversation item if it doesn't exist
        setConversationHistory(prev => {
          // Remove duplicates first
          const seenIds = new Set<string>();
          const deduplicated = prev.filter(conv => {
            if (seenIds.has(conv.id)) {
              console.log('Removing duplicate conversation before creating:', conv.id);
              return false;
            }
            seenIds.add(conv.id);
            return true;
          });
          
          const exists = deduplicated.some(item => item.id === convId);
          if (!exists) {
            const newItem = {
              id: convId!,
              query: currentQuery,
              sector: sector,
              plan: plan,
              selectedQuestions: selectedQuestions.length > 0 ? selectedQuestions : (plan?.questions || []),
              report: null,
              progressUpdates: [],
              researchStartTime: new Date(),
              researchDuration: null,
              status: 'planning',
              createdAt: new Date()
            };
            // Add to beginning of list so it appears at top
            console.log('Creating new conversation item in history:', convId, newItem.query);
            return [newItem, ...deduplicated];
          } else {
            // Update existing item to planning status and move to top
            console.log('Updating existing conversation item to planning:', convId);
            const updated = deduplicated.map(item => 
              item.id === convId 
                ? { ...item, status: 'planning', researchStartTime: new Date() }
                : item
            );
            // Move to top
            const updatedIndex = updated.findIndex(item => item.id === convId);
            if (updatedIndex > 0) {
              const updatedItem = updated[updatedIndex];
              updated.splice(updatedIndex, 1);
              updated.unshift(updatedItem);
            }
            return updated;
          }
        });
      }

    setIsResearching(true);
    setError(null);
    setStatus('planning');
    
    // Ensure conversation is visible in history with planning status
    if (convId) {
      setConversationHistory(prev => {
        const existingIndex = prev.findIndex(item => item.id === convId);
        if (existingIndex >= 0) {
          // Update existing to planning status
          const updated = [...prev];
          const existingItem = updated[existingIndex];
          updated.splice(existingIndex, 1);
          updated.unshift({
            ...existingItem,
            status: 'planning',
            researchStartTime: new Date()
          });
          console.log('Updated conversation to planning status:', convId);
          return updated;
        } else {
          // Create if doesn't exist (shouldn't happen, but be safe)
          console.log('Creating conversation in handleStartResearch:', convId);
          const newItem = {
            id: convId,
            query: currentQuery,
            sector: sector,
            plan: plan,
            selectedQuestions: selectedQuestions.length > 0 ? selectedQuestions : (plan?.questions || []),
            report: null,
            progressUpdates: [],
            researchStartTime: new Date(),
            researchDuration: null,
            status: 'planning',
            createdAt: new Date()
          };
          return [newItem, ...prev];
        }
      });
    }
    setProgressUpdates([]);
    setProgress(0);
    setStatus('planning');
    // Don't clear currentReport - keep it visible in conversation history
    const startTime = new Date();
    setResearchStartTime(startTime);
    setResearchDuration(null);
    
    // Update conversation item with research start
    if (convId) {
      setConversationHistory(prev => prev.map(item => 
        item.id === convId 
          ? { 
              ...item, 
              selectedQuestions: selectedQuestions.length > 0 ? selectedQuestions : (plan?.questions || []),
              researchStartTime: startTime,
              status: 'planning'
            }
          : item
      ));
    }

    try {
      const request: ResearchRequest = {
        query: currentQuery,
        sector,
        selected_questions: selectedQuestions.length > 0 ? selectedQuestions : (plan?.questions || []),
      };

      // Connect WebSocket and start research
      await researchWebSocket.connect(request);
    } catch (err: any) {
      setIsResearching(false);
      const errorMsg = err.message || 'Failed to start research';
      setError(errorMsg);
      console.error('Research start error:', err);
    }
  }, [currentQuery, sector, selectedQuestions, plan, currentConversationId]);

  const handleSelectReport = useCallback(async (queryId: string) => {
    try {
      const report = await getReport(queryId);
      
      // Restore full conversation context
      setCurrentQuery(report.query);
      setSector(report.sector as Sector);
      setCurrentReport(report);
      setStatus('completed');
      setProgress(1);
      setIsResearching(false);
      
      // Try to find the conversation item in current session history
      setConversationHistory(prev => {
        const existingItem = prev.find(item => item.report?.query_id === queryId);
        
        if (existingItem) {
          // Restore from existing conversation item
          setPlan(existingItem.plan);
          setSelectedQuestions(existingItem.selectedQuestions);
          setProgressUpdates(existingItem.progressUpdates);
          setResearchStartTime(existingItem.researchStartTime);
          setResearchDuration(existingItem.researchDuration);
          setCurrentConversationId(existingItem.id);
          return prev; // No change needed
        } else {
          // Create a new conversation item from the report
          // Note: Original plan and selected questions not stored in backend, so they'll be null/empty
          const convId = `conv-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
          setCurrentConversationId(convId);
          
          // Create a conversation item with the report
          const conversationItem: ConversationItem = {
            id: convId,
            query: report.query,
            sector: report.sector as Sector,
            plan: null, // Original plan not stored in backend
            selectedQuestions: [], // Original questions not stored in backend
            report: report,
            progressUpdates: [],
            researchStartTime: new Date(report.created_at),
            researchDuration: report.metadata.duration_seconds || null,
            status: 'completed',
            createdAt: new Date(report.created_at)
          };
          
          // Add to conversation history
          return [...prev, conversationItem];
        }
      });
      
      // Reload history after selecting a report (don't force - respect cleared state)
      await loadHistory(false);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load report';
      setError(errorMsg);
      console.error('Report load error:', err);
    }
  }, [loadHistory]);

  const clearHistory = useCallback(async () => {
    try {
      console.log('Clearing history...');
      
      // Delete all reports from backend
      await deleteAllReports();
      console.log('All reports deleted from backend');
      
      // Set flag to prevent reloads
      isHistoryClearedRef.current = true;
      setIsHistoryCleared(true);
      
      // Clear localStorage
      try {
        globalThis.localStorage.removeItem('research_history');
        globalThis.localStorage.setItem('research_history', JSON.stringify([]));
        // Also clear conversation history
        globalThis.localStorage.removeItem('conversation_history');
        globalThis.localStorage.setItem('conversation_history', JSON.stringify([]));
        globalThis.localStorage.removeItem('current_conversation_id');
        console.log('History and conversation history cleared from localStorage');
      } catch (localStorageError) {
        console.error('Failed to clear localStorage:', localStorageError);
      }
      
      // Clear history state
      setHistory([]);
      setConversationHistory([]);
      setCurrentConversationId(null);
      setCurrentReport(null);
      console.log('History cleared successfully');
    } catch (error) {
      console.error('Failed to clear history:', error);
      setError('Failed to clear history');
      setIsHistoryCleared(false);
      isHistoryClearedRef.current = false;
    }
  }, []);

  const deleteConversation = useCallback((conversationId: string) => {
    try {
      console.log('Deleting conversation:', conversationId);
      
      // Remove from conversation history
      setConversationHistory(prev => {
        const updated = prev.filter(conv => conv.id !== conversationId);
        return updated;
      });
      
      // If the deleted conversation was the current one, clear it
      if (currentConversationIdRef.current === conversationId) {
        setCurrentConversationId(null);
        currentConversationIdRef.current = null;
        setCurrentReport(null);
        setStatus('idle');
        setProgress(0);
      }
      
      console.log('Conversation deleted successfully');
    } catch (error: any) {
      console.error('Failed to delete conversation:', error);
      setError('Failed to delete conversation');
    }
  }, []);

  const deleteHistoryItem = useCallback(async (queryId: string) => {
    try {
      console.log('Deleting history item:', queryId);
      
      // Delete report from backend (only if it exists)
      try {
        await deleteReport(queryId);
        console.log('Report deleted from backend');
      } catch (deleteError: any) {
        // If report doesn't exist (e.g., in-progress query), that's okay
        if (deleteError.response?.status !== 404) {
          throw deleteError;
        }
        console.log('Report not found in backend (may be in-progress), continuing with local deletion');
      }
      
      // Remove from local state (history)
      setHistory(prev => prev.filter(report => report.query_id !== queryId));
      
      // Remove from conversation history
      setConversationHistory(prev => {
        const deletedConv = prev.find(conv => conv.report?.query_id === queryId);
        const updated = prev.filter(conv => conv.report?.query_id !== queryId);
        
        // If the deleted conversation was the current one, clear it
        if (deletedConv && currentConversationIdRef.current === deletedConv.id) {
          setCurrentConversationId(null);
          currentConversationIdRef.current = null;
        }
        
        return updated;
      });
      
      // If the deleted report was currently selected, clear selection
      if (currentReport?.query_id === queryId) {
        setCurrentReport(null);
        setStatus('idle');
        setProgress(0);
      }
      
      console.log('History item deleted successfully');
    } catch (error: any) {
      console.error('Failed to delete history item:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to delete report';
      setError(errorMsg);
    }
  }, [currentReport]);

  const reset = useCallback(() => {
    // Don't clear conversation history - just reset current state
    setCurrentQuery('');
    setSector(null);
    setPlan(null);
    setSelectedQuestions([]);
    setIsResearching(false);
    setCurrentReport(null);
    setProgressUpdates([]);
    setProgress(0);
    setStatus('idle');
    setError(null);
    setResearchStartTime(null);
    setResearchDuration(null);
    setCurrentConversationId(null);
    researchWebSocket.disconnect();
  }, []);

  const startNewResearch = useCallback(() => {
    // Save current conversation to history if there's any active state
    if (currentQuery || plan || currentReport || isResearching) {
      const currentConvId = currentConversationId || `conv-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
      
      // Create or update conversation item with current state
      const conversationItem: ConversationItem = {
        id: currentConvId,
        query: currentQuery || '',
        sector: sector,
        plan: plan,
        selectedQuestions: selectedQuestions,
        report: currentReport,
        progressUpdates: progressUpdates,
        researchStartTime: researchStartTime,
        researchDuration: researchDuration,
        status: isResearching ? 'researching' : (currentReport ? 'completed' : 'idle'),
        createdAt: researchStartTime || new Date()
      };
      
      // Add or update in conversation history
      setConversationHistory(prev => {
        const existingIndex = prev.findIndex(item => item.id === currentConvId);
        if (existingIndex >= 0) {
          // Update existing and move to top
          const updated = [...prev];
          const existingItem = updated[existingIndex];
          updated.splice(existingIndex, 1);
          updated.unshift({ ...existingItem, ...conversationItem });
          console.log('Updated existing conversation in history:', currentConvId);
          return updated;
        } else {
          // Add new to beginning
          console.log('Adding new conversation to history in startNewResearch:', currentConvId);
          return [conversationItem, ...prev];
        }
      });
    }
    
    // Now reset to start fresh conversation - IMPORTANT: Clear everything
    setCurrentQuery('');
    setSector(null);
    setPlan(null);
    setSelectedQuestions([]);
    setIsResearching(false);
    setCurrentReport(null);
    setProgressUpdates([]);
    setProgress(0);
    setStatus('idle');
    setError(null);
    setResearchStartTime(null);
    setResearchDuration(null);
    // CRITICAL: Set to null to ensure next query creates a NEW conversation
    setCurrentConversationId(null);
    researchWebSocket.disconnect();
  }, [currentQuery, plan, currentReport, isResearching, currentConversationId, sector, selectedQuestions, progressUpdates, researchStartTime, researchDuration]);

  const restoreConversation = useCallback((conversationId: string) => {
    const conv = conversationHistory.find(c => c.id === conversationId);
    if (conv) {
      setCurrentConversationId(conversationId);
      setCurrentQuery(conv.query);
      setSector(conv.sector);
      setPlan(conv.plan);
      setSelectedQuestions(conv.selectedQuestions);
      setCurrentReport(conv.report);
      setProgressUpdates(conv.progressUpdates);
      setResearchStartTime(conv.researchStartTime);
      setResearchDuration(conv.researchDuration);
      setIsResearching(conv.status === 'researching');
      setStatus(conv.status);
      setProgress(conv.status === 'completed' ? 1 : 0);
      
      // If there's a report, select it
      if (conv.report) {
        handleSelectReport(conv.report.query_id);
      }
    }
  }, [conversationHistory, handleSelectReport]);

    return {
    // State
    currentQuery,
    sector,
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
    
    // Actions
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
    setCurrentReport,
  };
}

