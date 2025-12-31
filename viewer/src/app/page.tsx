'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { WorkRelevanceDisplay } from "@/components/WorkRelevanceDisplay";
import { ToolResultsDisplay, ToolResult } from "@/components/ToolResultsDisplay";
import { FlagAccuracyDisplay } from "@/components/FlagAccuracyDisplay";
import { ClaimSupportDisplay, Claim } from "@/components/ClaimSupportDisplay";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useEffect, useState, useCallback, useRef, memo } from "react";

type FlagValue = 'FLAG' | 'NO FLAG' | 'UNDETERMINED';
type FlagType = 'affiliation' | 'institution' | 'domain' | 'sanctions';

interface GroundTruthFlags {
  affiliation: FlagValue;
  institution: FlagValue;
  domain: FlagValue;
  sanctions: FlagValue;
}

interface ComponentResult {
  pass: boolean;
  score: number;
  reason: string;
  quote?: string;
  metricName?: string;
  extractedSection?: string;
  toolResultIds?: string[];
  toolResults?: ToolResult[];
  errors: string[];
  llmEvaluation: string;
  workUrl?: string | null;
  passingSourceUrl?: string | null;
  extractedAiResponse?: string;
  workContent?: string;
  sourceEvaluations?: Array<{
    url: string;
    pass: boolean;
    score: number;
    reason: string;
    llmEvaluation: string;
  }>;
  extractedFlag?: FlagValue;
  groundTruthFlag?: FlagValue;
  allExtractedFlags?: GroundTruthFlags;
  allGroundTruthFlags?: GroundTruthFlags;
  claims?: Claim[];
}

interface TestResult {
  id: string;
  vars: {
    customer_info: string;
  };
  provider?: {
    id: string;
    label: string;
  };
  gradingResult: {
    pass: boolean;
    score: number;
    reason: string;
    componentResults: ComponentResult[];
  };
}

interface ResultsData {
  evalId: string;
  results: {
    version: number;
    timestamp: string;
    results: TestResult[];
  };
}

// Blind grading status - user grades without seeing original result
type GradingStatus = 'ungraded' | 'pass' | 'fail';

interface BlindGradingRecord {
  evalId: string;
  testId: string;
  assertionIndex: number;
  originalIndex: number; // Original index before randomization
  status: GradingStatus;
  timestamp: string;
  comment?: string;
  timeSpentMs?: number; // Time spent grading this case
}

interface ResultsFile {
  filename: string;
  mtime: string;
  mtimeMs: number;
}

const removeImagesFromMarkdown = (markdown: string): string => {
  return markdown.replace(/!\[.*?\]\(.*?\)/g, '');
};

interface AssertionDetailsProps {
  currentAssertion: ComponentResult;
  currentAssertionIndex: number;
  totalAssertions: number;
  gradingStatus: GradingStatus;
  comment?: string;
  removeImagesFromMarkdown: (markdown: string) => string;
  groundTruthFlag?: FlagValue;
  claimType?: FlagType | null;
}

const isWorkRelevanceMetric = (metricName?: string): boolean => {
  return metricName?.toUpperCase() === 'WORK-RELEVANCE';
};

const isFlagAccuracyMetric = (metricName?: string): boolean => {
  return metricName?.toUpperCase().includes('FLAG-ACCURACY') ?? false;
};

const isClaimSupportMetric = (metricName?: string): boolean => {
  return metricName?.toUpperCase().includes('CLAIM-SUPPORT') ?? false;
};

const extractClaimTypeFromMetric = (metricName?: string): FlagType | null => {
  if (!metricName) return null;
  const upper = metricName.toUpperCase();
  if (upper.includes('AFFILIATION')) return 'affiliation';
  if (upper.includes('INSTITUTION')) return 'institution';
  if (upper.includes('DOMAIN')) return 'domain';
  if (upper.includes('SANCTIONS')) return 'sanctions';
  return null;
};


const AssertionDetails = memo(function AssertionDetails({
  currentAssertion,
  currentAssertionIndex,
  totalAssertions,
  gradingStatus,
  comment,
  removeImagesFromMarkdown,
  groundTruthFlag,
  claimType,
}: AssertionDetailsProps) {
  return (
    <Card
      className={`border-l-4 ${
        gradingStatus === 'pass'
          ? 'border-l-green-500'
          : gradingStatus === 'fail'
          ? 'border-l-red-500'
          : 'border-l-gray-300'
      }`}
    >
      <CardHeader>
        <CardTitle className="flex items-center gap-3">
          <span>
            Assertion {currentAssertionIndex + 1} of {totalAssertions}
          </span>
          {currentAssertion.metricName && (
            <Badge variant="outline">{currentAssertion.metricName}</Badge>
          )}
          <Badge
            variant={
              gradingStatus === 'pass'
                ? 'default'
                : gradingStatus === 'fail'
                ? 'destructive'
                : 'secondary'
            }
          >
            {gradingStatus.toUpperCase()}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Show Extracted Section - this is the raw data to evaluate */}
        {currentAssertion.extractedSection && (
          <div>
            <h4 className="font-semibold text-lg mb-3">Extracted Section</h4>
            <div className="markdown">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {currentAssertion.extractedSection}
              </ReactMarkdown>
            </div>
          </div>
        )}

        {currentAssertion.toolResults && currentAssertion.toolResults.length > 0 && (
          <div>
            <h4 className="font-semibold text-lg mb-3">
              Tool Results ({currentAssertion.toolResults.length})
            </h4>
            <ToolResultsDisplay 
              toolResults={currentAssertion.toolResults}
              removeImagesFromMarkdown={removeImagesFromMarkdown}
            />
          </div>
        )}

        {currentAssertion.errors && currentAssertion.errors.length > 0 && (
          <div>
            <h4 className="font-semibold text-lg mb-3 text-red-700">Errors</h4>
            <ul className="text-sm text-red-700 space-y-2">
              {currentAssertion.errors.map((error, errorIndex) => (
                <li key={errorIndex} className="flex items-start">
                  <span className="text-red-500 mr-2">•</span>
                  {error}
                </li>
              ))}
            </ul>
          </div>
        )}

        {comment && (
          <div>
            <h4 className="font-semibold text-lg mb-3">Comment</h4>
            <div className="bg-blue-50 border border-blue-200 rounded p-4 text-sm whitespace-pre-wrap">
              {comment}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
});

// Generate a numeric hash from a string for seeding
function hashString(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return Math.abs(hash);
}

// Shuffle array using Fisher-Yates algorithm with a seeded random
function shuffleArray<T>(array: T[], seed: number): T[] {
  const shuffled = [...array];
  let currentSeed = seed;

  const seededRandom = () => {
    currentSeed = (currentSeed * 9301 + 49297) % 233280;
    return currentSeed / 233280;
  };

  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(seededRandom() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
}

// Format milliseconds as mm:ss
function formatTime(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

export default function Home() {
  const [resultsData, setResultsData] = useState<ResultsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [availableRuns, setAvailableRuns] = useState<ResultsFile[]>([]);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [currentTestIndex, setCurrentTestIndex] = useState(0);
  const [currentAssertionIndex, setCurrentAssertionIndex] = useState(0);

  // Randomized order: maps display index -> original test index
  const [shuffledIndices, setShuffledIndices] = useState<number[]>([]);

  // Blind grading state
  const [gradings, setGradings] = useState<Map<string, GradingStatus>>(new Map());
  const [comments, setComments] = useState<Map<string, string>>(new Map());
  const [isCommentModalOpen, setIsCommentModalOpen] = useState(false);
  const [commentText, setCommentText] = useState('');
  const commentTextRef = useRef(commentText);

  // Timer state
  const [caseStartTime, setCaseStartTime] = useState<number>(Date.now());
  const [currentElapsed, setCurrentElapsed] = useState<number>(0);
  const [completedTimes, setCompletedTimes] = useState<number[]>([]);

  // Ground truth for flag display (read-only in blind mode)
  const [groundTruthData, setGroundTruthData] = useState<GroundTruthFlags | null>(null);

  // Keep ref in sync to avoid re-creating callbacks on every keystroke
  useEffect(() => {
    commentTextRef.current = commentText;
  }, [commentText]);

  // Timer tick effect
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentElapsed(Date.now() - caseStartTime);
    }, 1000);
    return () => clearInterval(interval);
  }, [caseStartTime]);

  const getGradingKey = (testId: string, assertionIndex: number): string => {
    return `${testId}-${assertionIndex}`;
  };

  // Load available runs
  useEffect(() => {
    fetch('/api/results/list')
      .then(res => res.json())
      .then((files: ResultsFile[]) => {
        setAvailableRuns(files);
        if (files.length > 0 && !selectedRun) {
          setSelectedRun(files[0].filename);
        }
      })
      .catch(err => {
        console.error('Failed to load runs list:', err);
      });
  }, []);

  // Load results when selected run changes
  useEffect(() => {
    if (!selectedRun) return;

    setLoading(true);
    fetch(`/api/results?file=${encodeURIComponent(selectedRun)}`)
      .then(res => res.json())
      .then(data => {
        setResultsData(data);
        // Create shuffled indices for randomized display order
        // Use evalId as seed so order is consistent across page reloads
        const indices = Array.from({ length: data.results.results.length }, (_, i) => i);
        const seed = hashString(data.evalId || 'default');
        setShuffledIndices(shuffleArray(indices, seed));
        setCurrentTestIndex(0);
        setCurrentAssertionIndex(0);
        setCaseStartTime(Date.now());
        setCompletedTimes([]);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load results:', err);
        setLoading(false);
      });
  }, [selectedRun]);

  // Load existing blind gradings from filesystem
  useEffect(() => {
    if (!resultsData) return;

    fetch('/api/blind-gradings')
      .then(res => res.json())
      .then((records: BlindGradingRecord[]) => {
        const gradingMap = new Map<string, GradingStatus>();
        const commentMap = new Map<string, string>();

        records.forEach(record => {
          if (record.evalId === resultsData.evalId) {
            const key = getGradingKey(record.testId, record.assertionIndex);
            gradingMap.set(key, record.status);
            if (record.comment) {
              commentMap.set(key, record.comment);
            }
          }
        });

        setGradings(gradingMap);
        setComments(commentMap);
      })
      .catch(err => {
        console.error('Failed to load blind gradings:', err);
      });
  }, [resultsData]);

  // Update comment text when modal opens
  useEffect(() => {
    if (!resultsData || !isCommentModalOpen || shuffledIndices.length === 0) return;

    const originalIndex = shuffledIndices[currentTestIndex];
    const results = resultsData.results.results;
    const currentTest = results[originalIndex];
    if (!currentTest) return;

    const key = getGradingKey(currentTest.id, currentAssertionIndex);
    const currentComment = comments.get(key) || '';
    setCommentText(currentComment);
  }, [resultsData, currentTestIndex, currentAssertionIndex, isCommentModalOpen, comments, shuffledIndices]);

  // Handle grading toggle with useCallback to avoid stale closures
  const handleGradingToggle = useCallback(() => {
    if (!resultsData || shuffledIndices.length === 0) return;

    const originalIndex = shuffledIndices[currentTestIndex];
    const results = resultsData.results.results;
    const currentTest = results[originalIndex];
    if (!currentTest) return;

    const key = getGradingKey(currentTest.id, currentAssertionIndex);

    setGradings(prevGradings => {
      const currentStatus = prevGradings.get(key) || 'ungraded';
      // Cycle: ungraded -> pass -> fail -> ungraded
      const nextStatus: GradingStatus =
        currentStatus === 'ungraded' ? 'pass' :
        currentStatus === 'pass' ? 'fail' : 'ungraded';

      const newGradings = new Map(prevGradings);
      newGradings.set(key, nextStatus);

      // Get current comment if exists
      const currentComment = comments.get(key) || '';

      // Save to filesystem via API
      const record: BlindGradingRecord = {
        evalId: resultsData.evalId,
        testId: currentTest.id,
        assertionIndex: currentAssertionIndex,
        originalIndex: originalIndex,
        status: nextStatus,
        timestamp: new Date().toISOString(),
        comment: currentComment || undefined,
        timeSpentMs: currentElapsed,
      };

      fetch('/api/blind-gradings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(record),
      }).catch(err => {
        console.error('Failed to save grading:', err);
      });

      return newGradings;
    });
  }, [resultsData, currentTestIndex, currentAssertionIndex, shuffledIndices, comments, currentElapsed]);

  // Handle comment modal toggle
  const handleCommentModalToggle = useCallback(() => {
    if (!resultsData || shuffledIndices.length === 0) return;

    const originalIndex = shuffledIndices[currentTestIndex];
    const results = resultsData.results.results;
    const currentTest = results[originalIndex];
    if (!currentTest) return;

    const key = getGradingKey(currentTest.id, currentAssertionIndex);
    const textToSave = commentTextRef.current.trim();

    if (isCommentModalOpen) {
      // Closing modal - save comment
      setComments(prevComments => {
        const newComments = new Map(prevComments);
        const currentComment = prevComments.get(key) || '';

        if (textToSave !== currentComment) {
          if (textToSave) {
            newComments.set(key, textToSave);
          } else {
            newComments.delete(key);
          }

          // Save to filesystem via API
          const currentStatus = gradings.get(key) || 'ungraded';
          const record: BlindGradingRecord = {
            evalId: resultsData.evalId,
            testId: currentTest.id,
            assertionIndex: currentAssertionIndex,
            originalIndex: originalIndex,
            status: currentStatus,
            timestamp: new Date().toISOString(),
            comment: textToSave || undefined,
            timeSpentMs: currentElapsed,
          };

          fetch('/api/blind-gradings', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(record),
          }).catch(err => {
            console.error('Failed to save comment:', err);
          });
        }

        return newComments;
      });
      setIsCommentModalOpen(false);
    } else {
      // Opening modal - load current comment
      const currentComment = comments.get(key) || '';
      setCommentText(currentComment);
      setIsCommentModalOpen(true);
    }
  }, [resultsData, currentTestIndex, currentAssertionIndex, shuffledIndices, isCommentModalOpen, comments, gradings, currentElapsed]);

  // Record time when navigating to next test
  const recordTimeAndNavigate = useCallback((nextTestIndex: number) => {
    // Record time for current test if any assertion was graded
    const originalIndex = shuffledIndices[currentTestIndex];
    if (originalIndex !== undefined && resultsData) {
      const results = resultsData.results.results;
      const currentTest = results[originalIndex];
      if (currentTest) {
        const key = getGradingKey(currentTest.id, currentAssertionIndex);
        if (gradings.get(key) !== 'ungraded') {
          setCompletedTimes(prev => [...prev, currentElapsed]);
        }
      }
    }

    // Navigate and reset timer
    setCurrentTestIndex(nextTestIndex);
    setCurrentAssertionIndex(0);
    setCaseStartTime(Date.now());
  }, [shuffledIndices, currentTestIndex, currentAssertionIndex, resultsData, gradings, currentElapsed]);

  // Keyboard navigation
  useEffect(() => {
    if (!resultsData || shuffledIndices.length === 0) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (isCommentModalOpen && e.target instanceof HTMLTextAreaElement) {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          handleCommentModalToggle();
          return;
        }
        return;
      }

      const results = resultsData.results.results;
      const originalIndex = shuffledIndices[currentTestIndex];
      const currentTest = results[originalIndex];
      // Filter out FLAG-ACCURACY assertions for navigation
      const filteredAssertions = currentTest?.gradingResult.componentResults.filter(
        (a) => !isFlagAccuracyMetric(a.metricName)
      ) ?? [];

      switch (e.key) {
        case 'ArrowUp':
          e.preventDefault();
          if (currentTestIndex > 0) {
            recordTimeAndNavigate(currentTestIndex - 1);
          }
          break;
        case 'ArrowDown':
          e.preventDefault();
          if (currentTestIndex < shuffledIndices.length - 1) {
            recordTimeAndNavigate(currentTestIndex + 1);
          }
          break;
        case 'ArrowLeft':
          e.preventDefault();
          setCurrentAssertionIndex(prev => Math.max(0, prev - 1));
          break;
        case 'ArrowRight':
          e.preventDefault();
          if (filteredAssertions.length > 0) {
            setCurrentAssertionIndex(prev => Math.min(filteredAssertions.length - 1, prev + 1));
          }
          break;
        case ' ':
          e.preventDefault();
          handleGradingToggle();
          break;
        case 'Enter':
          e.preventDefault();
          handleCommentModalToggle();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    resultsData,
    shuffledIndices,
    currentTestIndex,
    currentAssertionIndex,
    handleGradingToggle,
    handleCommentModalToggle,
    recordTimeAndNavigate,
    isCommentModalOpen,
  ]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
          <p className="mt-4 text-gray-600">Loading evaluation results...</p>
        </div>
      </div>
    );
  }

  if (!resultsData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600">Failed to load evaluation results.</p>
        </div>
      </div>
    );
  }

  const results = resultsData.results.results;
  // Use shuffled indices for blind grading
  const originalIndex = shuffledIndices[currentTestIndex] ?? 0;
  const currentTest = results[originalIndex];

  // Filter out FLAG-ACCURACY assertions - they don't need validation
  const filteredAssertions = currentTest?.gradingResult.componentResults.filter(
    (a) => !isFlagAccuracyMetric(a.metricName)
  ) ?? [];
  const currentAssertion = filteredAssertions[currentAssertionIndex];

  const getCurrentGradingStatus = (): GradingStatus => {
    const key = getGradingKey(currentTest.id, currentAssertionIndex);
    return gradings.get(key) || 'ungraded';
  };
  const totalAssertions = filteredAssertions.length;
  const currentGradingStatus = currentAssertion ? getCurrentGradingStatus() : 'ungraded';
  const currentComment = currentAssertion
    ? comments.get(getGradingKey(currentTest.id, currentAssertionIndex))
    : undefined;

  // Calculate grading progress
  const gradedCount = Array.from(gradings.values()).filter(s => s !== 'ungraded').length;
  const totalCases = shuffledIndices.length;

  // Calculate average time
  const averageTime = completedTimes.length > 0
    ? completedTimes.reduce((a, b) => a + b, 0) / completedTimes.length
    : 0;

  // Get current claim type and ground truth flag for flag accuracy metrics (read-only)
  const currentClaimType = currentAssertion ? extractClaimTypeFromMetric(currentAssertion.metricName) : null;
  const currentGroundTruthFlag = currentAssertion?.allGroundTruthFlags?.[currentClaimType!] ?? 'UNDETERMINED';

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Blind Grading Mode
          </h1>
          <p className="text-gray-600">
            Progress: {gradedCount} / {totalCases} cases graded
          </p>
        </div>

        {/* Timer Display */}
        <div className="flex justify-center gap-8">
          <div className="text-center">
            <div className="text-2xl font-mono font-bold text-blue-600">
              {formatTime(currentElapsed)}
            </div>
            <div className="text-sm text-gray-500">Current Case</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-mono font-bold text-green-600">
              {completedTimes.length > 0 ? formatTime(averageTime) : '--:--'}
            </div>
            <div className="text-sm text-gray-500">Avg Time ({completedTimes.length} cases)</div>
          </div>
        </div>

        {/* Navigation - simplified for blind grading */}
        <div className="flex gap-4 justify-center items-center">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Run:</label>
            <select
              value={selectedRun || ''}
              onChange={(e) => setSelectedRun(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {availableRuns.map((run) => (
                <option key={run.filename} value={run.filename}>
                  {run.filename}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Case:</label>
            <select
              value={currentTestIndex}
              onChange={(e) => recordTimeAndNavigate(Number(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {shuffledIndices.map((_, displayIndex) => (
                <option key={displayIndex} value={displayIndex}>
                  Case {displayIndex + 1}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Assertion:</label>
            <select
              value={currentAssertionIndex}
              onChange={(e) => setCurrentAssertionIndex(Number(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {filteredAssertions.map((_, index) => (
                <option key={index} value={index}>
                  Assertion {index + 1}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Keyboard Navigation Help */}
        <div className="text-center text-sm text-gray-500">
          ↑↓ navigate cases • ←→ assertions • Space cycle PASS/FAIL/UNGRADED • Enter comment
        </div>

        {/* Current Test Case Overview - NO model/score info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <span>Case {currentTestIndex + 1} of {totalCases}</span>
            </CardTitle>
            <CardDescription>
              <div className="mt-2">
                <span className="text-sm whitespace-pre-wrap">
                  {currentTest.vars.customer_info}
                </span>
              </div>
            </CardDescription>
          </CardHeader>
        </Card>

        {/* Current Assertion */}
        {currentAssertion && (
          <AssertionDetails
            currentAssertion={currentAssertion}
            currentAssertionIndex={currentAssertionIndex}
            totalAssertions={totalAssertions}
            gradingStatus={currentGradingStatus}
            comment={currentComment}
            removeImagesFromMarkdown={removeImagesFromMarkdown}
            groundTruthFlag={currentGroundTruthFlag}
            claimType={currentClaimType}
          />
        )}

        {/* Comment Modal */}
        {isCommentModalOpen && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            onClick={(e) => {
              if (e.target === e.currentTarget) {
                handleCommentModalToggle();
              }
            }}
          >
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] flex flex-col">
              <div className="p-6 border-b">
                <h2 className="text-xl font-semibold">Add Comment</h2>
                <p className="text-sm text-gray-500 mt-1">
                  Case {currentTestIndex + 1}, Assertion {currentAssertionIndex + 1}
                </p>
              </div>
              <div className="p-6 flex-1 overflow-y-auto">
                <textarea
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  placeholder="Enter your comment here... (Press Enter to save and close, Shift+Enter for new line)"
                  className="w-full h-64 p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      e.stopPropagation();
                      handleCommentModalToggle();
                    }
                  }}
                />
              </div>
              <div className="p-6 border-t flex justify-end gap-3">
                <button
                  onClick={handleCommentModalToggle}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCommentModalToggle}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  Save (Enter)
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Footer */}
        <div className="text-center text-sm text-gray-400">
          Case {currentTestIndex + 1} of {totalCases} •
          Assertion {currentAssertionIndex + 1} of {totalAssertions}
        </div>
      </div>
    </div>
  );
}