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

interface GroundTruthRecord {
  customerInfoPreview: string;
  flags: GroundTruthFlags;
  notes: string;
  lastReviewed: string | null;
}

interface GroundTruthData {
  version: string;
  created: string;
  lastUpdated: string;
  records: Record<string, GroundTruthRecord>;
}

interface ComponentResult {
  pass: boolean;
  score: number;
  reason: string;
  quote?: string;
  metricName?: string;
  extractedSection?: string;  // Optional - not present in work relevance assertions
  toolResultIds?: string[];
  toolResults?: ToolResult[];
  errors: string[];
  llmEvaluation: string;
  // Work relevance specific fields
  workUrl?: string | null;
  passingSourceUrl?: string | null;
  extractedAiResponse?: string;
  workContent?: string;  // Reference work content for work relevance
  sourceEvaluations?: Array<{  // Individual source evaluations for work relevance
    url: string;
    pass: boolean;
    score: number;
    reason: string;
    llmEvaluation: string;
  }>;
  // Flag accuracy specific fields
  extractedFlag?: FlagValue;
  groundTruthFlag?: FlagValue;
  allExtractedFlags?: GroundTruthFlags;
  allGroundTruthFlags?: GroundTruthFlags;
  // Claim support specific fields
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

type AgreementStatus = 'unreviewed' | 'correct' | 'incorrect';

interface AgreementRecord {
  evalId: string;
  testId: string;
  assertionIndex: number;
  providerId: string;
  promptId: string;
  status: AgreementStatus;
  timestamp: string;
  comment?: string;
  model_comments?: string;
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
  agreementStatus: AgreementStatus;
  comment?: string;
  modelComment?: string;
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
  agreementStatus,
  comment,
  modelComment,
  removeImagesFromMarkdown,
  groundTruthFlag,
  claimType,
}: AssertionDetailsProps) {
  return (
    <Card
      className={`border-l-4 ${
        agreementStatus === 'correct'
          ? 'border-l-green-500'
          : agreementStatus === 'incorrect'
          ? 'border-l-red-500'
          : 'border-l-gray-300'
      }`}
    >
      <CardHeader>
        <CardTitle className="flex items-center gap-3">
          <span>
            Assertion {currentAssertionIndex + 1} of {totalAssertions}
          </span>
          <Badge variant={currentAssertion.pass ? 'default' : 'destructive'}>
            {currentAssertion.pass ? 'PASS' : 'FAIL'}
          </Badge>
          {currentAssertion.metricName && (
            <Badge variant="outline">{currentAssertion.metricName}</Badge>
          )}
          <Badge
            variant={
              agreementStatus === 'correct'
                ? 'default'
                : agreementStatus === 'incorrect'
                ? 'destructive'
                : 'secondary'
            }
          >
            {agreementStatus.toUpperCase()}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* For claim support metrics, show Extracted Section first */}
        {isClaimSupportMetric(currentAssertion.metricName) && currentAssertion.extractedSection && (
          <div>
            <h4 className="font-semibold text-lg mb-3">Extracted Section</h4>
            <div className="markdown">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {currentAssertion.extractedSection}
              </ReactMarkdown>
            </div>
          </div>
        )}

        <div>
          <h4 className="font-semibold text-lg mb-3">Reason</h4>
          {isWorkRelevanceMetric(currentAssertion.metricName) ? (
            <WorkRelevanceDisplay 
              reason={currentAssertion.reason} 
              workUrl={currentAssertion.workUrl}
              passingSourceUrl={currentAssertion.passingSourceUrl}
              extractedAiResponse={currentAssertion.extractedAiResponse}
            />
          ) : isFlagAccuracyMetric(currentAssertion.metricName) ? (
            <FlagAccuracyDisplay
              extractedFlag={currentAssertion.extractedFlag || 'UNDETERMINED'}
              groundTruthFlag={groundTruthFlag || currentAssertion.groundTruthFlag || 'UNDETERMINED'}
              reason={currentAssertion.reason}
              claimType={claimType || 'affiliation'}
            />
          ) : isClaimSupportMetric(currentAssertion.metricName) ? (
            <ClaimSupportDisplay
              reason={currentAssertion.reason}
              claims={currentAssertion.claims}
            />
          ) : (
            <div className="markdown">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {currentAssertion.reason}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* For non-claim-support metrics, show Extracted Section after Reason */}
        {!isClaimSupportMetric(currentAssertion.metricName) && currentAssertion.extractedSection && (
          <div>
            <h4 className="font-semibold text-lg mb-3">Extracted Section</h4>
            <div className="markdown">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {currentAssertion.extractedSection}
              </ReactMarkdown>
            </div>
          </div>
        )}

        {currentAssertion.quote && (
          <div>
            <h4 className="font-semibold text-lg mb-3">Supporting Quote</h4>
            <div className="markdown">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {currentAssertion.quote}
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

        {modelComment && (
          <div>
            <h4 className="font-semibold text-lg mb-3">Model Comment</h4>
            <div className="bg-purple-50 border border-purple-200 rounded p-4 text-sm whitespace-pre-wrap">
              {modelComment}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
});

export default function Home() {
  const [resultsData, setResultsData] = useState<ResultsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [availableRuns, setAvailableRuns] = useState<ResultsFile[]>([]);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [currentTestIndex, setCurrentTestIndex] = useState(0);
  const [currentAssertionIndex, setCurrentAssertionIndex] = useState(0);
  const [agreements, setAgreements] = useState<Map<string, AgreementStatus>>(new Map());
  const [comments, setComments] = useState<Map<string, string>>(new Map());
  const [modelComments, setModelComments] = useState<Map<string, string>>(new Map());
  const [isCommentModalOpen, setIsCommentModalOpen] = useState(false);
  const [isModelCommentModalOpen, setIsModelCommentModalOpen] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [modelCommentText, setModelCommentText] = useState('');
  const commentTextRef = useRef(commentText);
  const modelCommentTextRef = useRef(modelCommentText);
  const [groundTruthData, setGroundTruthData] = useState<GroundTruthData | null>(null);
  const [customerToRecordKey, setCustomerToRecordKey] = useState<Map<string, string>>(new Map());
  const [flagUpdateFeedback, setFlagUpdateFeedback] = useState<{ flag: FlagValue; claimType: FlagType } | null>(null);

  // Keep ref in sync to avoid re-creating callbacks on every keystroke
  useEffect(() => {
    commentTextRef.current = commentText;
  }, [commentText]);

  useEffect(() => {
    modelCommentTextRef.current = modelCommentText;
  }, [modelCommentText]);

  const getAgreementKey = (testId: string, assertionIndex: number): string => {
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

  // Load ground truth data
  useEffect(() => {
    fetch('/api/ground-truth')
      .then(res => res.json())
      .then((data: GroundTruthData) => {
        setGroundTruthData(data);
      })
      .catch(err => {
        console.error('Failed to load ground truth:', err);
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
        setCurrentTestIndex(0);
        setCurrentAssertionIndex(0);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load results:', err);
        setLoading(false);
      });
  }, [selectedRun]);

  // Load agreements and comments from filesystem
  useEffect(() => {
    if (!resultsData) return;

    fetch('/api/agreements')
      .then(res => res.json())
      .then((records: AgreementRecord[]) => {
        const agreementMap = new Map<string, AgreementStatus>();
        const commentMap = new Map<string, string>();
        const modelCommentMap = new Map<string, string>();

        records.forEach(record => {
          if (record.evalId === resultsData.evalId) {
            const key = getAgreementKey(record.testId, record.assertionIndex);
            agreementMap.set(key, record.status);
            if (record.comment) {
              commentMap.set(key, record.comment);
            }
            if (record.model_comments) {
              modelCommentMap.set(key, record.model_comments);
            }
          }
        });

        setAgreements(agreementMap);
        setComments(commentMap);
        setModelComments(modelCommentMap);
      })
      .catch(err => {
        console.error('Failed to load agreements:', err);
      });
  }, [resultsData]);

  // Update comment text when modal opens or test/assertion changes
  useEffect(() => {
    if (!resultsData || !isCommentModalOpen) return;
    
    const results = resultsData.results.results;
    const currentTest = results[currentTestIndex];
    if (!currentTest) return;

    const key = getAgreementKey(currentTest.id, currentAssertionIndex);
    const currentComment = comments.get(key) || '';
    setCommentText(currentComment);
  }, [resultsData, currentTestIndex, currentAssertionIndex, isCommentModalOpen, comments]);

  useEffect(() => {
    if (!resultsData || !isModelCommentModalOpen) return;

    const results = resultsData.results.results;
    const currentTest = results[currentTestIndex];
    if (!currentTest) return;

    const key = getAgreementKey(currentTest.id, currentAssertionIndex);
    const currentModelComment = modelComments.get(key) || '';
    setModelCommentText(currentModelComment);
  }, [resultsData, currentTestIndex, currentAssertionIndex, isModelCommentModalOpen, modelComments]);

  // Handle agreement toggle with useCallback to avoid stale closures
  const handleAgreementToggle = useCallback(() => {
    if (!resultsData) return;
    
    const results = resultsData.results.results;
    const currentTest = results[currentTestIndex];
    if (!currentTest) return;

    const key = getAgreementKey(currentTest.id, currentAssertionIndex);
    
    setAgreements(prevAgreements => {
      const currentStatus = prevAgreements.get(key) || 'unreviewed';
      const nextStatus: AgreementStatus =
        currentStatus === 'unreviewed' ? 'correct' :
        currentStatus === 'correct' ? 'incorrect' : 'unreviewed';

      const newAgreements = new Map(prevAgreements);
      newAgreements.set(key, nextStatus);

      // Get current comment if exists
      const currentComment = comments.get(key) || '';
      const currentModelComment = modelComments.get(key) || '';

      // Save to filesystem via API
      const record: AgreementRecord = {
        evalId: resultsData.evalId,
        testId: currentTest.id,
        assertionIndex: currentAssertionIndex,
        providerId: currentTest.id || 'unknown',
        promptId: currentTest.id || 'unknown',
        status: nextStatus,
        timestamp: new Date().toISOString(),
        comment: currentComment || undefined,
        model_comments: currentModelComment || undefined
      };

      fetch('/api/agreements', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(record),
      }).catch(err => {
        console.error('Failed to save agreement:', err);
      });

      return newAgreements;
    });
  }, [resultsData, currentTestIndex, currentAssertionIndex, comments, modelComments]);

  // Handle comment modal toggle
  const handleCommentModalToggle = useCallback(() => {
    if (!resultsData) return;
    
    const results = resultsData.results.results;
    const currentTest = results[currentTestIndex];
    if (!currentTest) return;

    const key = getAgreementKey(currentTest.id, currentAssertionIndex);
    const textToSave = commentTextRef.current.trim();
    const existingModelComment = modelComments.get(key) || '';

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
          const currentStatus = agreements.get(key) || 'unreviewed';
          const record: AgreementRecord = {
            evalId: resultsData.evalId,
            testId: currentTest.id,
            assertionIndex: currentAssertionIndex,
            providerId: currentTest.id || 'unknown',
            promptId: currentTest.id || 'unknown',
            status: currentStatus,
            timestamp: new Date().toISOString(),
            comment: textToSave || undefined,
            model_comments: existingModelComment || undefined
          };

          fetch('/api/agreements', {
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
      setIsModelCommentModalOpen(false);
      setIsCommentModalOpen(true);
    }
  }, [resultsData, currentTestIndex, currentAssertionIndex, isCommentModalOpen, comments, modelComments, agreements]);

  const handleModelCommentModalToggle = useCallback(() => {
    if (!resultsData) return;

    const results = resultsData.results.results;
    const currentTest = results[currentTestIndex];
    if (!currentTest) return;

    const key = getAgreementKey(currentTest.id, currentAssertionIndex);
    const textToSave = modelCommentTextRef.current.trim();
    const existingComment = comments.get(key) || '';

    if (isModelCommentModalOpen) {
      setModelComments(prevModelComments => {
        const newModelComments = new Map(prevModelComments);
        const currentModelComment = prevModelComments.get(key) || '';

        if (textToSave !== currentModelComment) {
          if (textToSave) {
            newModelComments.set(key, textToSave);
          } else {
            newModelComments.delete(key);
          }

          const currentStatus = agreements.get(key) || 'unreviewed';
          const record: AgreementRecord = {
            evalId: resultsData.evalId,
            testId: currentTest.id,
            assertionIndex: currentAssertionIndex,
            providerId: currentTest.id || 'unknown',
            promptId: currentTest.id || 'unknown',
            status: currentStatus,
            timestamp: new Date().toISOString(),
            comment: existingComment || undefined,
            model_comments: textToSave || undefined,
          };

          fetch('/api/agreements', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(record),
          }).catch(err => {
            console.error('Failed to save model comment:', err);
          });
        }

        return newModelComments;
      });
      setIsModelCommentModalOpen(false);
    } else {
      const currentModelComment = modelComments.get(key) || '';
      setModelCommentText(currentModelComment);
      setIsModelCommentModalOpen(true);
      setIsCommentModalOpen(false);
    }
  }, [resultsData, currentTestIndex, currentAssertionIndex, isModelCommentModalOpen, modelComments, comments, agreements]);

  // Helper to get current flag from ground truth data
  const getCurrentFlagFromGroundTruth = useCallback((customerInfo: string, claimType: FlagType): FlagValue => {
    // First check if we have a cached record key
    const recordKey = customerToRecordKey.get(customerInfo);
    if (recordKey && groundTruthData?.records[recordKey]) {
      return groundTruthData.records[recordKey].flags[claimType];
    }
    
    // Fall back to searching by customerInfoPreview
    if (groundTruthData) {
      for (const [key, record] of Object.entries(groundTruthData.records)) {
        if (customerInfo.includes(record.customerInfoPreview.substring(0, 50).replace('...', ''))) {
          return record.flags[claimType];
        }
      }
    }
    
    return 'UNDETERMINED';
  }, [groundTruthData, customerToRecordKey]);

  // Handle ground truth flag toggle
  const handleFlagToggle = useCallback(() => {
    if (!resultsData) return;

    const results = resultsData.results.results;
    const currentTest = results[currentTestIndex];
    if (!currentTest) return;

    const currentAssertion = currentTest.gradingResult.componentResults[currentAssertionIndex];
    if (!currentAssertion || !isFlagAccuracyMetric(currentAssertion.metricName)) return;

    const claimType = extractClaimTypeFromMetric(currentAssertion.metricName);
    if (!claimType) return;

    const customerInfo = currentTest.vars.customer_info;

    // Get current flag from our ground truth state (not from static assertion data)
    const currentFlag = getCurrentFlagFromGroundTruth(customerInfo, claimType);

    // Cycle: UNDETERMINED -> FLAG -> NO FLAG -> UNDETERMINED
    const nextFlag: FlagValue = 
      currentFlag === 'UNDETERMINED' ? 'FLAG' :
      currentFlag === 'FLAG' ? 'NO FLAG' : 'UNDETERMINED';

    // Update via API
    fetch('/api/ground-truth', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        customerInfo,
        flagType: claimType,
        value: nextFlag,
      }),
    })
      .then(res => res.json())
      .then(data => {
        if (data.success && data.recordKey) {
          // Store the customer -> recordKey mapping
          setCustomerToRecordKey(prev => {
            const newMap = new Map(prev);
            newMap.set(customerInfo, data.recordKey);
            return newMap;
          });

          // Update local ground truth data
          setGroundTruthData(prev => {
            if (!prev) return prev;
            const newData = { ...prev };
            if (newData.records[data.recordKey]) {
              newData.records[data.recordKey] = {
                ...newData.records[data.recordKey],
                flags: data.updatedFlags,
              };
            } else {
              // Create new record
              newData.records[data.recordKey] = {
                customerInfoPreview: customerInfo.substring(0, 100) + '...',
                flags: data.updatedFlags,
                notes: '',
                lastReviewed: new Date().toISOString(),
              };
            }
            return newData;
          });

          // Show feedback with the actual saved value from the API response
          const savedFlag = data.updatedFlags[claimType] as FlagValue;
          setFlagUpdateFeedback({ flag: savedFlag, claimType });
          
          // Clear feedback after 2 seconds
          setTimeout(() => {
            setFlagUpdateFeedback(null);
          }, 2000);
        }
      })
      .catch(err => {
        console.error('Failed to update ground truth flag:', err);
      });
  }, [resultsData, currentTestIndex, currentAssertionIndex, getCurrentFlagFromGroundTruth]);

  // Keyboard navigation
  useEffect(() => {
    if (!resultsData) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      const isAnyModalOpen = isCommentModalOpen || isModelCommentModalOpen;
      if (isAnyModalOpen && e.target instanceof HTMLTextAreaElement) {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          if (isCommentModalOpen) {
            handleCommentModalToggle();
          } else if (isModelCommentModalOpen) {
            handleModelCommentModalToggle();
          }
          return;
        }
        return;
      }

      const results = resultsData.results.results;
      const currentTest = results[currentTestIndex];

      switch (e.key) {
        case 'ArrowUp':
          e.preventDefault();
          setCurrentTestIndex(prev => Math.max(0, prev - 1));
          setCurrentAssertionIndex(0);
          break;
        case 'ArrowDown':
          e.preventDefault();
          setCurrentTestIndex(prev => Math.min(results.length - 1, prev + 1));
          setCurrentAssertionIndex(0);
          break;
        case 'ArrowLeft':
          e.preventDefault();
          setCurrentAssertionIndex(prev => Math.max(0, prev - 1));
          break;
        case 'ArrowRight':
          e.preventDefault();
          if (currentTest) {
            setCurrentAssertionIndex(prev => Math.min(currentTest.gradingResult.componentResults.length - 1, prev + 1));
          }
          break;
        case ' ':
          e.preventDefault();
          handleAgreementToggle();
          break;
        case 'Enter':
          e.preventDefault();
          handleCommentModalToggle();
          break;
        case 'M':
        case 'm':
          e.preventDefault();
          handleModelCommentModalToggle();
          break;
        case 'F':
        case 'f':
          e.preventDefault();
          handleFlagToggle();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    resultsData,
    currentTestIndex,
    currentAssertionIndex,
    handleAgreementToggle,
    handleCommentModalToggle,
    handleModelCommentModalToggle,
    handleFlagToggle,
    isCommentModalOpen,
    isModelCommentModalOpen,
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
  const currentTest = results[currentTestIndex];
  const currentAssertion = currentTest?.gradingResult.componentResults[currentAssertionIndex];
  const getCurrentAgreementStatus = (): AgreementStatus => {
    const key = getAgreementKey(currentTest.id, currentAssertionIndex);
    return agreements.get(key) || 'unreviewed';
  };
  const totalAssertions = currentTest?.gradingResult.componentResults.length ?? 0;
  const currentAgreementStatus = currentAssertion ? getCurrentAgreementStatus() : 'unreviewed';
  const currentComment = currentAssertion
    ? comments.get(getAgreementKey(currentTest.id, currentAssertionIndex))
    : undefined;
  const currentModelComment = currentAssertion
    ? modelComments.get(getAgreementKey(currentTest.id, currentAssertionIndex))
    : undefined;

  // Get current claim type and ground truth flag for flag accuracy metrics
  const currentClaimType = currentAssertion ? extractClaimTypeFromMetric(currentAssertion.metricName) : null;
  const currentGroundTruthFlag = (() => {
    if (!currentAssertion || !currentClaimType || !currentTest) return undefined;
    
    // Prioritize groundTruthData (live state) over static assertion data
    const customerInfo = currentTest.vars.customer_info;
    
    // First check cached record key
    const recordKey = customerToRecordKey.get(customerInfo);
    if (recordKey && groundTruthData?.records[recordKey]) {
      return groundTruthData.records[recordKey].flags[currentClaimType];
    }
    
    // Search in groundTruthData by customerInfoPreview
    if (groundTruthData) {
      for (const [, record] of Object.entries(groundTruthData.records)) {
        if (customerInfo.includes(record.customerInfoPreview.substring(0, 50).replace('...', ''))) {
          return record.flags[currentClaimType];
        }
      }
    }
    
    // Fall back to assertion's static data
    if (currentAssertion.allGroundTruthFlags?.[currentClaimType]) {
      return currentAssertion.allGroundTruthFlags[currentClaimType];
    }
    
    return 'UNDETERMINED';
  })();

  const getCustomerName = (customerInfo: string): string => {
    const nameMatch = customerInfo.match(/Name:\s*(.+)/);
    return nameMatch ? nameMatch[1].trim() : "Unknown Customer";
  };

  const getCustomerInstitution = (customerInfo: string): string => {
    const institutionMatch = customerInfo.match(/Institution:\s*(.+)/);
    return institutionMatch ? institutionMatch[1].trim() : "Unknown Institution";
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            KYC Evaluation Results
          </h1>
          <p className="text-gray-600">
            Evaluation ID: {resultsData.evalId} •{" "}
            {results.length} test cases •{" "}
            Generated: {new Date(resultsData.results.timestamp).toLocaleDateString()}
          </p>
        </div>

        {/* Navigation Dropdowns */}
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
                  {run.filename} ({new Date(run.mtime).toLocaleString()})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Test Case:</label>
            <select
              value={currentTestIndex}
              onChange={(e) => {
                setCurrentTestIndex(Number(e.target.value));
                setCurrentAssertionIndex(0);
              }}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {results.map((result, index) => (
                <option key={result.id} value={index}>
                  Test {index + 1}: {getCustomerName(result.vars.customer_info)}
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
              {currentTest?.gradingResult.componentResults.map((_, index) => (
                <option key={index} value={index}>
                  Assertion {index + 1}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Keyboard Navigation Help */}
        <div className="text-center text-sm text-gray-500">
          ↑↓ test cases • ←→ assertions • Space agree/disagree • Enter comment • f cycle flag
        </div>

        {/* Current Test Case Overview */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-3">
                <span>Test Case {currentTestIndex + 1}</span>
                {currentTest.provider?.label && (
                  <Badge variant="outline">
                    {currentTest.provider.label}
                  </Badge>
                )}
                <span className="text-sm font-normal text-gray-500">
                  Score: {currentTest.gradingResult.score.toFixed(2)}
                </span>
              </CardTitle>
            </div>
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
            agreementStatus={currentAgreementStatus}
            comment={currentComment}
            modelComment={currentModelComment}
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
                  Test Case {currentTestIndex + 1}, Assertion {currentAssertionIndex + 1}
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

        {/* Model Comment Modal */}
        {isModelCommentModalOpen && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            onClick={(e) => {
              if (e.target === e.currentTarget) {
                handleModelCommentModalToggle();
              }
            }}
          >
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] flex flex-col">
              <div className="p-6 border-b">
                <h2 className="text-xl font-semibold">Add Model Comment</h2>
                <p className="text-sm text-gray-500 mt-1">
                  Test Case {currentTestIndex + 1}, Assertion {currentAssertionIndex + 1}
                </p>
              </div>
              <div className="p-6 flex-1 overflow-y-auto">
                <textarea
                  value={modelCommentText}
                  onChange={(e) => setModelCommentText(e.target.value)}
                  placeholder="Enter model comment here... (Press Enter to save and close, Shift+Enter for new line)"
                  className="w-full h-64 p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      e.stopPropagation();
                      handleModelCommentModalToggle();
                    }
                  }}
                />
              </div>
              <div className="p-6 border-t flex justify-end gap-3">
                <button
                  onClick={handleModelCommentModalToggle}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Cancel
                </button>
                <button
                  onClick={handleModelCommentModalToggle}
                  className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  Save (Enter)
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Footer */}
        <div className="text-center text-sm text-gray-400">
          Test {currentTestIndex + 1} of {results.length} •
          Assertion {currentAssertionIndex + 1} of {currentTest?.gradingResult.componentResults.length || 0}
        </div>
      </div>

      {/* Flag Update Feedback Toast */}
      {flagUpdateFeedback && (
        <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-2 fade-in duration-300">
          <div className={`px-4 py-3 rounded-lg shadow-lg border flex items-center gap-3 ${
            flagUpdateFeedback.flag === 'FLAG' 
              ? 'bg-red-50 border-red-300 text-red-800'
              : flagUpdateFeedback.flag === 'NO FLAG'
              ? 'bg-green-50 border-green-300 text-green-800'
              : 'bg-yellow-50 border-yellow-300 text-yellow-800'
          }`}>
            <span className="font-medium">
              {flagUpdateFeedback.claimType.charAt(0).toUpperCase() + flagUpdateFeedback.claimType.slice(1)} ground truth set to:
            </span>
            <span className={`px-2 py-0.5 rounded text-sm font-bold ${
              flagUpdateFeedback.flag === 'FLAG'
                ? 'bg-red-200'
                : flagUpdateFeedback.flag === 'NO FLAG'
                ? 'bg-green-200'
                : 'bg-yellow-200'
            }`}>
              {flagUpdateFeedback.flag}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}