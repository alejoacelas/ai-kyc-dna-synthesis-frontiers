'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ToolResultsDisplay, ToolResult } from "@/components/ToolResultsDisplay";
import { FlagAccuracyDisplay } from "@/components/FlagAccuracyDisplay";
import { ClaimSupportDisplay, Claim } from "@/components/ClaimSupportDisplay";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useEffect, useState, memo, useRef, useCallback } from "react";

type FlagValue = 'FLAG' | 'NO FLAG' | 'UNDETERMINED';
type FlagType = 'affiliation' | 'institution' | 'domain' | 'sanctions';
type ErrorCategory = 'empty_response' | 'information_not_found' | 'flag_instructions_not_followed' | 'difference_in_judgment' | 'factual_mistake' | null;

// Error categories in cycle order
const ERROR_CATEGORIES: ErrorCategory[] = [
  null,
  'empty_response',
  'information_not_found',
  'flag_instructions_not_followed',
  'difference_in_judgment',
  'factual_mistake',
];

const ERROR_CATEGORY_LABELS: Record<string, string> = {
  'empty_response': 'Empty response',
  'information_not_found': 'Information not found',
  'flag_instructions_not_followed': 'Flag instructions not followed',
  'difference_in_judgment': 'Difference in judgment',
  'factual_mistake': 'Factual mistake',
};

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

interface FlagErrorRecord {
  id: string;
  timestamp: string;
  lastUpdated: string;
  customerName: string;
  customerInfoPreview: string;
  provider: string;
  flagType: FlagType | 'unknown';
  extractedFlag: FlagValue;
  groundTruthFlag: FlagValue;
  metricName: string;
  comment: string | null;
  errorCategory: ErrorCategory;
  isCorrectProvider: boolean;
  extractedModelResponse: string | null;
}

interface RecordsData {
  version: string;
  created: string;
  lastUpdated: string;
  records: FlagErrorRecord[];
}

// Flag types in order
const FLAG_TYPES_ORDER: FlagType[] = ['affiliation', 'institution', 'domain', 'sanctions'];

// Metric types in order within each flag type
const METRIC_ORDER = ['FLAG-ACCURACY', 'SOURCE-RELIABILITY', 'CLAIM-SUPPORT'];

// Flag type to related metrics mapping
const FLAG_TYPE_METRICS: Record<FlagType, string[]> = {
  affiliation: ['AFFILIATION-FLAG-ACCURACY', 'AFFILIATION-SOURCE-RELIABILITY', 'AFFILIATION-CLAIM-SUPPORT'],
  institution: ['INSTITUTION-FLAG-ACCURACY', 'INSTITUTION-SOURCE-RELIABILITY', 'INSTITUTION-CLAIM-SUPPORT'],
  domain: ['DOMAIN-FLAG-ACCURACY', 'DOMAIN-SOURCE-RELIABILITY', 'DOMAIN-CLAIM-SUPPORT'],
  sanctions: ['SANCTIONS-FLAG-ACCURACY', 'SANCTIONS-SOURCE-RELIABILITY', 'SANCTIONS-CLAIM-SUPPORT'],
};

// All metrics for correct providers (show all flag-related assertions)
const ALL_FLAG_METRICS = [
  'AFFILIATION-FLAG-ACCURACY', 'AFFILIATION-SOURCE-RELIABILITY', 'AFFILIATION-CLAIM-SUPPORT',
  'INSTITUTION-FLAG-ACCURACY', 'INSTITUTION-SOURCE-RELIABILITY', 'INSTITUTION-CLAIM-SUPPORT',
  'DOMAIN-FLAG-ACCURACY', 'DOMAIN-SOURCE-RELIABILITY', 'DOMAIN-CLAIM-SUPPORT',
  'SANCTIONS-FLAG-ACCURACY', 'SANCTIONS-SOURCE-RELIABILITY', 'SANCTIONS-CLAIM-SUPPORT',
];

interface FlagError {
  flagType: FlagType;
  extractedFlag: FlagValue;
  groundTruthFlag: FlagValue;
}

interface ProviderResult {
  provider: string;
  testResult: TestResult;
  flagErrors: FlagError[];
  relevantAssertions: ComponentResult[];
  isCorrect: boolean;
}

interface CustomerWithErrors {
  customerInfo: string;
  customerName: string;
  failedProviders: ProviderResult[];
  correctProviders: ProviderResult[];
  recordKey: string;
  // Provider agreement counts per flag type
  flagAgreement: Record<FlagType, { FLAG: number; 'NO FLAG': number; UNDETERMINED: number }>;
  // Ground truth flags for this customer
  groundTruthFlags: GroundTruthFlags | null;
  // Whether any ground truth is UNDETERMINED
  hasUndeterminedGroundTruth: boolean;
  // Total number of failed providers (for high disagreement filter)
  totalFailedProviderCount: number;
}

type FilterMode = 'all' | 'undetermined' | 'high_disagreement';
type ViewMode = 'failed' | 'correct' | 'all';

const removeImagesFromMarkdown = (markdown: string): string => {
  return markdown.replace(/!\[.*?\]\(.*?\)/g, '');
};

const isFlagAccuracyMetric = (metricName?: string): boolean => {
  return metricName?.toUpperCase().includes('FLAG-ACCURACY') ?? false;
};

const isClaimSupportMetric = (metricName?: string): boolean => {
  return metricName?.toUpperCase().includes('CLAIM-SUPPORT') ?? false;
};

const extractFlagTypeFromMetric = (metricName?: string): FlagType | null => {
  if (!metricName) return null;
  const upper = metricName.toUpperCase();
  if (upper.includes('AFFILIATION')) return 'affiliation';
  if (upper.includes('INSTITUTION')) return 'institution';
  if (upper.includes('DOMAIN')) return 'domain';
  if (upper.includes('SANCTIONS')) return 'sanctions';
  return null;
};

const extractMetricType = (metricName?: string): string | null => {
  if (!metricName) return null;
  const upper = metricName.toUpperCase();
  if (upper.includes('FLAG-ACCURACY')) return 'FLAG-ACCURACY';
  if (upper.includes('SOURCE-RELIABILITY')) return 'SOURCE-RELIABILITY';
  if (upper.includes('CLAIM-SUPPORT')) return 'CLAIM-SUPPORT';
  return null;
};

// Sort assertions: group by flag type, then order FLAG-ACCURACY, SOURCE-RELIABILITY, CLAIM-SUPPORT
function sortAssertions(assertions: ComponentResult[]): ComponentResult[] {
  return [...assertions].sort((a, b) => {
    const flagTypeA = extractFlagTypeFromMetric(a.metricName);
    const flagTypeB = extractFlagTypeFromMetric(b.metricName);
    const metricTypeA = extractMetricType(a.metricName);
    const metricTypeB = extractMetricType(b.metricName);

    const flagOrderA = flagTypeA ? FLAG_TYPES_ORDER.indexOf(flagTypeA) : 999;
    const flagOrderB = flagTypeB ? FLAG_TYPES_ORDER.indexOf(flagTypeB) : 999;
    if (flagOrderA !== flagOrderB) return flagOrderA - flagOrderB;

    const metricOrderA = metricTypeA ? METRIC_ORDER.indexOf(metricTypeA) : 999;
    const metricOrderB = metricTypeB ? METRIC_ORDER.indexOf(metricTypeB) : 999;
    return metricOrderA - metricOrderB;
  });
}

// Generate record key for looking up saved data
function getRecordKey(customerName: string, provider: string, flagType: string): string {
  return `${customerName}|${provider}|${flagType}`;
}

interface AssertionDetailsProps {
  assertion: ComponentResult;
  index: number;
  total: number;
  removeImagesFromMarkdown: (markdown: string) => string;
  liveGroundTruthFlag?: FlagValue;
  isCorrectWithLiveGT?: boolean;
}

const AssertionDetails = memo(function AssertionDetails({
  assertion,
  index,
  total,
  removeImagesFromMarkdown,
  liveGroundTruthFlag,
  isCorrectWithLiveGT,
}: AssertionDetailsProps) {
  const flagType = extractFlagTypeFromMetric(assertion.metricName);
  // Use live ground truth if provided, otherwise fall back to embedded value
  const displayGroundTruth = liveGroundTruthFlag ?? assertion.groundTruthFlag ?? 'UNDETERMINED';
  // Determine pass/fail based on live ground truth
  const isPass = isCorrectWithLiveGT ?? assertion.pass;

  return (
    <Card className={`border-l-4 ${isPass ? 'border-l-green-500' : 'border-l-red-500'}`}>
      <CardHeader>
        <CardTitle className="flex items-center gap-3">
          <span>
            Assertion {index + 1} of {total}
          </span>
          {assertion.metricName && (
            <Badge variant="outline">{assertion.metricName}</Badge>
          )}
          <Badge variant={isPass ? 'default' : 'destructive'}>
            {isPass ? 'PASS' : 'FAIL'}
          </Badge>
          {flagType && (
            <Badge variant="secondary" className="capitalize">{flagType}</Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Flag Accuracy Display */}
        {isFlagAccuracyMetric(assertion.metricName) && (
          <FlagAccuracyDisplay
            extractedFlag={assertion.extractedFlag ?? 'UNDETERMINED'}
            groundTruthFlag={displayGroundTruth}
            reason={assertion.reason}
            claimType={extractFlagTypeFromMetric(assertion.metricName) ?? 'unknown'}
          />
        )}

        {/* Extracted Section */}
        {assertion.extractedSection && !isFlagAccuracyMetric(assertion.metricName) && (
          <div>
            <h4 className="font-semibold text-lg mb-3">Extracted Section</h4>
            <div className="markdown bg-gray-50 p-4 rounded border">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {assertion.extractedSection}
              </ReactMarkdown>
            </div>
          </div>
        )}

        {/* Claim Support Display */}
        {isClaimSupportMetric(assertion.metricName) && (
          <ClaimSupportDisplay
            reason={assertion.reason}
            claims={assertion.claims}
          />
        )}

        {/* Source Reliability / Other metrics */}
        {!isFlagAccuracyMetric(assertion.metricName) && !isClaimSupportMetric(assertion.metricName) && assertion.reason && (
          <div>
            <h4 className="font-semibold text-lg mb-3">AI Reasoning</h4>
            <div className="bg-gray-50 border border-gray-200 rounded p-4">
              <div className="markdown text-sm">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {assertion.reason}
                </ReactMarkdown>
              </div>
            </div>
            {assertion.llmEvaluation && (
              <div className="mt-4 bg-blue-50 border border-blue-200 rounded p-4">
                <h5 className="font-medium text-sm text-blue-600 mb-2">LLM Evaluation</h5>
                <div className="markdown text-sm">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {assertion.llmEvaluation}
                  </ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tool Results */}
        {assertion.toolResults && assertion.toolResults.length > 0 && (
          <div>
            <h4 className="font-semibold text-lg mb-3">
              Tool Results ({assertion.toolResults.length})
            </h4>
            <ToolResultsDisplay
              toolResults={assertion.toolResults}
              removeImagesFromMarkdown={removeImagesFromMarkdown}
            />
          </div>
        )}

        {/* Errors */}
        {assertion.errors && assertion.errors.length > 0 && (
          <div>
            <h4 className="font-semibold text-lg mb-3 text-red-700">Errors</h4>
            <ul className="text-sm text-red-700 space-y-2">
              {assertion.errors.map((error, errorIndex) => (
                <li key={errorIndex} className="flex items-start">
                  <span className="text-red-500 mr-2">•</span>
                  {error}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
});

// Comment Modal Component
interface CommentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (comment: string) => void;
  customerName: string;
  provider: string;
  flagType: FlagType | null;
  metricName: string;
  extractedFlag: FlagValue;
  groundTruthFlag: FlagValue;
  existingComment: string | null;
}

function CommentModal({
  isOpen,
  onClose,
  onSubmit,
  customerName,
  provider,
  flagType,
  metricName,
  extractedFlag,
  groundTruthFlag,
  existingComment,
}: CommentModalProps) {
  const [comment, setComment] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (isOpen) {
      setComment(existingComment || '');
      if (textareaRef.current) {
        textareaRef.current.focus();
      }
    }
  }, [isOpen, existingComment]);

  const handleSubmit = () => {
    if (comment.trim()) {
      onSubmit(comment.trim());
      onClose();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    } else if (e.key === 'Enter' && e.metaKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-6" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-xl font-bold mb-4">{existingComment ? 'Edit Comment' : 'Add Comment'}</h2>

        <div className="mb-4 space-y-2 text-sm text-gray-600">
          <div><span className="font-medium">Customer:</span> {customerName}</div>
          <div><span className="font-medium">Provider:</span> {provider}</div>
          <div><span className="font-medium">Flag Type:</span> <span className="capitalize">{flagType || 'N/A'}</span></div>
          <div><span className="font-medium">Metric:</span> {metricName}</div>
          <div className="flex gap-4">
            <span><span className="font-medium">Extracted:</span> {extractedFlag}</span>
            <span><span className="font-medium">Ground Truth:</span> {groundTruthFlag}</span>
          </div>
        </div>

        <textarea
          ref={textareaRef}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter your comment about this flag error..."
          className="w-full h-32 p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        />

        <div className="mt-4 flex justify-between items-center">
          <span className="text-xs text-gray-400">Cmd+Enter to submit, Esc to cancel</span>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-900 rounded-md"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={!comment.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Save Comment
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function FlagErrorsPage() {
  const [loading, setLoading] = useState(true);
  const [allCustomersWithErrors, setAllCustomersWithErrors] = useState<CustomerWithErrors[]>([]);
  const [customersWithErrors, setCustomersWithErrors] = useState<CustomerWithErrors[]>([]);
  const [allProviders, setAllProviders] = useState<string[]>([]);
  const [currentCustomerIndex, setCurrentCustomerIndex] = useState(0);
  const [currentProviderIndex, setCurrentProviderIndex] = useState(0);
  const [currentAssertionIndex, setCurrentAssertionIndex] = useState(0);
  const [viewMode, setViewMode] = useState<ViewMode>('failed');
  const [commentModalOpen, setCommentModalOpen] = useState(false);
  const [savedRecords, setSavedRecords] = useState<Map<string, FlagErrorRecord>>(new Map());

  // New state for filters and ground truth editing
  const [filterMode, setFilterMode] = useState<FilterMode>('all');
  const [disagreementThreshold, setDisagreementThreshold] = useState(6);
  const [groundTruthModified, setGroundTruthModified] = useState(false);
  const [localGroundTruth, setLocalGroundTruth] = useState<GroundTruthData | null>(null);
  const [resultsData, setResultsData] = useState<ResultsData | null>(null);

  // Load data
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const [resultsRes, groundTruthRes, recordsRes] = await Promise.all([
          fetch('/api/results?file=human_baseline_subset_main.json'),
          fetch('/api/ground-truth'),
          fetch('/api/flag-error-comments'),
        ]);

        const resultsData: ResultsData = await resultsRes.json();
        const gtData: GroundTruthData = await groundTruthRes.json();
        const recordsData: RecordsData = await recordsRes.json();

        // Build map of saved records
        const recordsMap = new Map<string, FlagErrorRecord>();
        for (const record of recordsData.records || []) {
          const key = getRecordKey(record.customerName, record.provider, record.flagType);
          recordsMap.set(key, record);
        }
        setSavedRecords(recordsMap);

        const providers = new Set<string>();
        for (const testResult of resultsData.results.results) {
          if (testResult.provider?.label) {
            providers.add(testResult.provider.label);
          }
        }
        setAllProviders(Array.from(providers).sort());
        setResultsData(resultsData);
        setLocalGroundTruth(gtData);

        const allFiltered = findCustomersWithFlagErrors(resultsData, gtData);
        setAllCustomersWithErrors(allFiltered);
        setCustomersWithErrors(allFiltered);
        setCurrentCustomerIndex(0);
        setCurrentProviderIndex(0);
        setCurrentAssertionIndex(0);
      } catch (err) {
        console.error('Failed to load data:', err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  function findCustomersWithFlagErrors(
    resultsData: ResultsData,
    gtData: GroundTruthData
  ): CustomerWithErrors[] {
    const customerMap = new Map<string, TestResult[]>();

    for (const testResult of resultsData.results.results) {
      const customerInfo = testResult.vars.customer_info;
      if (!customerMap.has(customerInfo)) {
        customerMap.set(customerInfo, []);
      }
      customerMap.get(customerInfo)!.push(testResult);
    }

    const results: CustomerWithErrors[] = [];

    for (const [customerInfo, testResults] of customerMap) {
      const failedProviders: ProviderResult[] = [];
      const correctProviders: ProviderResult[] = [];
      let recordKey = '';
      let groundTruthFlags: GroundTruthFlags | null = null;

      const normalized = customerInfo.toLowerCase().replace(/\s+/g, ' ').trim();
      for (const [key, record] of Object.entries(gtData.records)) {
        const previewNormalized = record.customerInfoPreview.toLowerCase().replace(/\s+/g, ' ').trim();
        if (normalized.startsWith(previewNormalized.substring(0, 50))) {
          recordKey = key;
          groundTruthFlags = record.flags;
          break;
        }
      }

      // Initialize flag agreement counters
      const flagAgreement: Record<FlagType, { FLAG: number; 'NO FLAG': number; UNDETERMINED: number }> = {
        affiliation: { FLAG: 0, 'NO FLAG': 0, UNDETERMINED: 0 },
        institution: { FLAG: 0, 'NO FLAG': 0, UNDETERMINED: 0 },
        domain: { FLAG: 0, 'NO FLAG': 0, UNDETERMINED: 0 },
        sanctions: { FLAG: 0, 'NO FLAG': 0, UNDETERMINED: 0 },
      };

      for (const testResult of testResults) {
        const provider = testResult.provider?.label ?? 'Unknown';

        const flagAccuracyResults = testResult.gradingResult.componentResults.filter(
          c => isFlagAccuracyMetric(c.metricName)
        );

        const firstFlagAccuracy = flagAccuracyResults[0];
        if (!firstFlagAccuracy?.allExtractedFlags) continue;

        const extracted = firstFlagAccuracy.allExtractedFlags;
        // Use live ground truth from gtData, not embedded in test results
        const liveGroundTruth = groundTruthFlags || {
          affiliation: 'UNDETERMINED' as FlagValue,
          institution: 'UNDETERMINED' as FlagValue,
          domain: 'UNDETERMINED' as FlagValue,
          sanctions: 'UNDETERMINED' as FlagValue,
        };

        // Count provider flags for agreement summary
        const flagTypes: FlagType[] = ['affiliation', 'institution', 'domain', 'sanctions'];
        for (const flagType of flagTypes) {
          const extractedVal = extracted[flagType] ?? 'UNDETERMINED';
          flagAgreement[flagType][extractedVal]++;
        }

        const flagErrors: FlagError[] = [];

        for (const flagType of flagTypes) {
          const extractedVal = extracted[flagType] ?? 'UNDETERMINED';
          const groundTruthVal = liveGroundTruth[flagType] ?? 'UNDETERMINED';
          if (extractedVal !== groundTruthVal) {
            flagErrors.push({
              flagType,
              extractedFlag: extractedVal,
              groundTruthFlag: groundTruthVal,
            });
          }
        }

        if (flagErrors.length === 0) {
          const allAssertions = testResult.gradingResult.componentResults.filter(
            c => c.metricName && ALL_FLAG_METRICS.includes(c.metricName.toUpperCase())
          );

          correctProviders.push({
            provider,
            testResult,
            flagErrors: [],
            relevantAssertions: sortAssertions(allAssertions),
            isCorrect: true,
          });
        } else {
          const relevantMetricNames = new Set<string>();
          for (const error of flagErrors) {
            for (const metric of FLAG_TYPE_METRICS[error.flagType]) {
              relevantMetricNames.add(metric);
            }
          }

          const relevantAssertions = testResult.gradingResult.componentResults.filter(
            c => c.metricName && relevantMetricNames.has(c.metricName.toUpperCase())
          );

          failedProviders.push({
            provider,
            testResult,
            flagErrors,
            relevantAssertions: sortAssertions(relevantAssertions),
            isCorrect: false,
          });
        }
      }

      // Check if any ground truth is UNDETERMINED
      const hasUndeterminedGroundTruth = groundTruthFlags
        ? Object.values(groundTruthFlags).some(v => v === 'UNDETERMINED')
        : true;

      if (failedProviders.length > 0) {
        const customerName = customerInfo.split('\n')[0].replace('Name: ', '');

        results.push({
          customerInfo,
          customerName,
          failedProviders,
          correctProviders,
          recordKey,
          flagAgreement,
          groundTruthFlags,
          hasUndeterminedGroundTruth,
          totalFailedProviderCount: failedProviders.length,
        });
      }
    }

    results.sort((a, b) => a.customerName.localeCompare(b.customerName));
    return results;
  }

  // Recompute customers when ground truth changes
  useEffect(() => {
    if (!resultsData || !localGroundTruth) return;

    const allFiltered = findCustomersWithFlagErrors(resultsData, localGroundTruth);
    setAllCustomersWithErrors(allFiltered);
    // Don't reset navigation indices here - we want to stay on the same customer
  }, [localGroundTruth, resultsData]);

  // Filter customers based on filterMode
  useEffect(() => {
    if (allCustomersWithErrors.length === 0) return;

    let filtered = allCustomersWithErrors;

    if (filterMode === 'undetermined') {
      filtered = allCustomersWithErrors.filter(c => c.hasUndeterminedGroundTruth);
    } else if (filterMode === 'high_disagreement') {
      filtered = allCustomersWithErrors.filter(c => c.totalFailedProviderCount >= disagreementThreshold);
    }

    setCustomersWithErrors(filtered);
  }, [filterMode, disagreementThreshold, allCustomersWithErrors]);

  // Reset indices when filtered customers change and current index is out of bounds
  useEffect(() => {
    if (customersWithErrors.length > 0 && currentCustomerIndex >= customersWithErrors.length) {
      setCurrentCustomerIndex(0);
      setCurrentProviderIndex(0);
      setCurrentAssertionIndex(0);
    }
  }, [customersWithErrors.length, currentCustomerIndex]);

  const getCurrentProviders = useCallback((customer: CustomerWithErrors): ProviderResult[] => {
    if (viewMode === 'all') {
      // Combine and sort by provider name
      return [...customer.failedProviders, ...customer.correctProviders].sort((a, b) =>
        a.provider.localeCompare(b.provider)
      );
    }
    return viewMode === 'correct' ? customer.correctProviders : customer.failedProviders;
  }, [viewMode]);

  // Get current flag type's record key
  const getCurrentRecordKey = useCallback(() => {
    if (!customersWithErrors.length) return null;
    const currentCustomer = customersWithErrors[currentCustomerIndex];
    const currentProviders = getCurrentProviders(currentCustomer);
    const currentProviderResult = currentProviders[currentProviderIndex];
    const currentAssertion = currentProviderResult?.relevantAssertions[currentAssertionIndex];
    if (!currentAssertion) return null;

    const flagType = extractFlagTypeFromMetric(currentAssertion.metricName);
    if (!flagType) return null;

    return getRecordKey(currentCustomer.customerName, currentProviderResult.provider, flagType);
  }, [customersWithErrors, currentCustomerIndex, currentProviderIndex, currentAssertionIndex, getCurrentProviders]);

  // Get extracted model response for current flag type
  const getExtractedModelResponse = useCallback(() => {
    if (!customersWithErrors.length) return null;
    const currentCustomer = customersWithErrors[currentCustomerIndex];
    const currentProviders = getCurrentProviders(currentCustomer);
    const currentProviderResult = currentProviders[currentProviderIndex];
    if (!currentProviderResult) return null;

    const currentAssertion = currentProviderResult.relevantAssertions[currentAssertionIndex];
    const flagType = extractFlagTypeFromMetric(currentAssertion?.metricName);
    if (!flagType) return null;

    // Find the source-reliability or claim-support assertion for this flag type to get extractedSection
    const relevantAssertion = currentProviderResult.relevantAssertions.find(a => {
      const ft = extractFlagTypeFromMetric(a.metricName);
      const mt = extractMetricType(a.metricName);
      return ft === flagType && (mt === 'SOURCE-RELIABILITY' || mt === 'CLAIM-SUPPORT');
    });

    return relevantAssertion?.extractedSection || null;
  }, [customersWithErrors, currentCustomerIndex, currentProviderIndex, currentAssertionIndex, getCurrentProviders]);

  // Save record (category or comment)
  const saveRecord = async (updates: { comment?: string; errorCategory?: ErrorCategory }) => {
    if (!customersWithErrors.length) return;

    const currentCustomer = customersWithErrors[currentCustomerIndex];
    const currentProviders = getCurrentProviders(currentCustomer);
    const currentProviderResult = currentProviders[currentProviderIndex];
    const currentAssertion = currentProviderResult?.relevantAssertions[currentAssertionIndex];

    if (!currentAssertion) return;

    const flagType = extractFlagTypeFromMetric(currentAssertion.metricName);
    if (!flagType) return;

    // Find the flag error for this flag type
    const flagError = currentProviderResult.flagErrors.find(e => e.flagType === flagType);

    try {
      const response = await fetch('/api/flag-error-comments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customerName: currentCustomer.customerName,
          customerInfoPreview: currentCustomer.customerInfo.substring(0, 200),
          provider: currentProviderResult.provider,
          flagType,
          extractedFlag: flagError?.extractedFlag || currentAssertion.extractedFlag || 'UNDETERMINED',
          groundTruthFlag: flagError?.groundTruthFlag || currentAssertion.groundTruthFlag || 'UNDETERMINED',
          metricName: currentAssertion.metricName || '',
          isCorrectProvider: currentProviderResult.isCorrect,
          extractedModelResponse: getExtractedModelResponse(),
          ...updates,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save record');
      }

      const result = await response.json();

      // Update local state
      const key = getRecordKey(currentCustomer.customerName, currentProviderResult.provider, flagType);
      setSavedRecords(prev => {
        const newMap = new Map(prev);
        newMap.set(key, result.record);
        return newMap;
      });
    } catch (err) {
      console.error('Failed to save record:', err);
    }
  };

  // Handle space key - cycle error category
  const handleCycleCategory = useCallback(async () => {
    const key = getCurrentRecordKey();
    if (!key) return;

    const currentRecord = savedRecords.get(key);
    const currentCategory = currentRecord?.errorCategory || null;
    const currentIndex = ERROR_CATEGORIES.indexOf(currentCategory);
    const nextIndex = (currentIndex + 1) % ERROR_CATEGORIES.length;
    const nextCategory = ERROR_CATEGORIES[nextIndex];

    await saveRecord({ errorCategory: nextCategory });
  }, [getCurrentRecordKey, savedRecords]);

  // Handle 'f' key - cycle ground truth flag value
  const handleCycleGroundTruth = useCallback(async () => {
    if (!customersWithErrors.length) return;
    const currentCustomer = customersWithErrors[currentCustomerIndex];
    const currentProviders = getCurrentProviders(currentCustomer);
    const currentProviderResult = currentProviders[currentProviderIndex];
    const currentAssertion = currentProviderResult?.relevantAssertions[currentAssertionIndex];

    if (!currentAssertion) return;

    const flagType = extractFlagTypeFromMetric(currentAssertion.metricName);
    if (!flagType) return;

    // Get current ground truth value
    const currentGroundTruth = currentAssertion.groundTruthFlag || 'UNDETERMINED';

    // Cycle: FLAG → NO FLAG → UNDETERMINED → FLAG
    const cycle: FlagValue[] = ['FLAG', 'NO FLAG', 'UNDETERMINED'];
    const currentIdx = cycle.indexOf(currentGroundTruth);
    const nextIdx = (currentIdx + 1) % cycle.length;
    const nextValue = cycle[nextIdx];

    try {
      const response = await fetch('/api/ground-truth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recordKey: currentCustomer.recordKey,
          customerInfo: currentCustomer.customerInfo,
          flagType,
          value: nextValue,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save ground truth');
      }

      const result = await response.json();

      // Update local ground truth state
      if (localGroundTruth && result.recordKey) {
        setLocalGroundTruth(prev => {
          if (!prev) return prev;
          return {
            ...prev,
            lastUpdated: new Date().toISOString(),
            records: {
              ...prev.records,
              [result.recordKey]: {
                ...prev.records[result.recordKey],
                flags: result.updatedFlags,
              },
            },
          };
        });
      }

      // Update the customersWithErrors to reflect the new ground truth
      const updatedFlags = result.updatedFlags as GroundTruthFlags;
      const hasUndetermined = (Object.values(updatedFlags) as FlagValue[]).some(v => v === 'UNDETERMINED');

      setCustomersWithErrors(prev => prev.map((customer, idx) => {
        if (idx !== currentCustomerIndex) return customer;
        return {
          ...customer,
          groundTruthFlags: updatedFlags,
          hasUndeterminedGroundTruth: hasUndetermined,
        };
      }));

      // Also update allCustomersWithErrors
      setAllCustomersWithErrors(prev => prev.map(customer => {
        if (customer.recordKey !== currentCustomer.recordKey) return customer;
        return {
          ...customer,
          groundTruthFlags: updatedFlags,
          hasUndeterminedGroundTruth: hasUndetermined,
        };
      }));

      setGroundTruthModified(true);
    } catch (err) {
      console.error('Failed to save ground truth:', err);
    }
  }, [customersWithErrors, currentCustomerIndex, currentProviderIndex, currentAssertionIndex, getCurrentProviders, localGroundTruth]);

  // Handle comment save
  const handleSaveComment = async (comment: string) => {
    await saveRecord({ comment });
  };

  // Keyboard navigation
  useEffect(() => {
    if (customersWithErrors.length === 0) return;
    if (commentModalOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      const currentCustomer = customersWithErrors[currentCustomerIndex];
      if (!currentCustomer) return;

      const currentProviders = getCurrentProviders(currentCustomer);
      const currentProviderResult = currentProviders[currentProviderIndex];

      switch (e.key) {
        case 'ArrowUp':
          e.preventDefault();
          if (currentCustomerIndex > 0) {
            const newCustomer = customersWithErrors[currentCustomerIndex - 1];
            const newProviders = getCurrentProviders(newCustomer);
            if (newProviders.length === 0 && viewMode !== 'all') {
              setViewMode('failed');
            }
            setCurrentCustomerIndex(currentCustomerIndex - 1);
            setCurrentProviderIndex(0);
            setCurrentAssertionIndex(0);
          }
          break;
        case 'ArrowDown':
          e.preventDefault();
          if (currentCustomerIndex < customersWithErrors.length - 1) {
            const newCustomer = customersWithErrors[currentCustomerIndex + 1];
            const newProviders = getCurrentProviders(newCustomer);
            if (newProviders.length === 0 && viewMode !== 'all') {
              setViewMode('failed');
            }
            setCurrentCustomerIndex(currentCustomerIndex + 1);
            setCurrentProviderIndex(0);
            setCurrentAssertionIndex(0);
          }
          break;
        case 'ArrowLeft':
          e.preventDefault();
          if (!currentProviderResult) break;
          if (currentAssertionIndex > 0) {
            setCurrentAssertionIndex(currentAssertionIndex - 1);
          } else if (currentProviderIndex > 0) {
            const prevProvider = currentProviders[currentProviderIndex - 1];
            setCurrentProviderIndex(currentProviderIndex - 1);
            setCurrentAssertionIndex(prevProvider.relevantAssertions.length - 1);
          }
          break;
        case 'ArrowRight':
          e.preventDefault();
          if (!currentProviderResult) break;
          if (currentAssertionIndex < currentProviderResult.relevantAssertions.length - 1) {
            setCurrentAssertionIndex(currentAssertionIndex + 1);
          } else if (currentProviderIndex < currentProviders.length - 1) {
            setCurrentProviderIndex(currentProviderIndex + 1);
            setCurrentAssertionIndex(0);
          }
          break;
        case 'Tab':
          e.preventDefault();
          // Cycle through: failed -> correct -> all -> failed
          const modes: ViewMode[] = ['failed', 'correct', 'all'];
          const currentModeIndex = modes.indexOf(viewMode);
          let nextModeIndex = (currentModeIndex + 1) % modes.length;
          // Skip modes with no providers (except 'all' which always has providers)
          for (let i = 0; i < modes.length; i++) {
            const candidateMode = modes[nextModeIndex];
            if (candidateMode === 'all') break;
            const candidateProviders = candidateMode === 'correct'
              ? currentCustomer.correctProviders
              : currentCustomer.failedProviders;
            if (candidateProviders.length > 0) break;
            nextModeIndex = (nextModeIndex + 1) % modes.length;
          }
          setViewMode(modes[nextModeIndex]);
          setCurrentProviderIndex(0);
          setCurrentAssertionIndex(0);
          break;
        case 'Enter':
          e.preventDefault();
          setCommentModalOpen(true);
          break;
        case ' ':
          e.preventDefault();
          handleCycleCategory();
          break;
        case 'f':
          e.preventDefault();
          handleCycleGroundTruth();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [customersWithErrors, currentCustomerIndex, currentProviderIndex, currentAssertionIndex, viewMode, commentModalOpen, getCurrentProviders, handleCycleCategory, handleCycleGroundTruth]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
          <p className="mt-4 text-gray-600">Loading flag error analysis...</p>
        </div>
      </div>
    );
  }

  if (customersWithErrors.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Flag Error Analysis</h1>
          <p className="text-gray-600">No flag errors found in the human baseline subset.</p>
        </div>
      </div>
    );
  }

  const currentCustomer = customersWithErrors[currentCustomerIndex];
  const currentProviders = getCurrentProviders(currentCustomer);
  const currentProviderResult = currentProviders[currentProviderIndex];
  const currentAssertion = currentProviderResult?.relevantAssertions[currentAssertionIndex];

  let globalAssertionIndex = currentAssertionIndex;
  for (let i = 0; i < currentProviderIndex; i++) {
    globalAssertionIndex += currentProviders[i].relevantAssertions.length;
  }
  const totalAssertions = currentProviders.reduce((sum, p) => sum + p.relevantAssertions.length, 0);

  const currentFlagType = currentAssertion ? extractFlagTypeFromMetric(currentAssertion.metricName) : null;
  const currentRecordKey = currentFlagType
    ? getRecordKey(currentCustomer.customerName, currentProviderResult?.provider || '', currentFlagType)
    : null;
  const currentRecord = currentRecordKey ? savedRecords.get(currentRecordKey) : null;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Regeneration Banner */}
        {groundTruthModified && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
            <span className="text-amber-500 text-xl">⚠️</span>
            <div>
              <p className="font-medium text-amber-800">Ground truth modified</p>
              <p className="text-sm text-amber-700 mt-1">To update figures, run:</p>
              <code className="text-xs bg-amber-100 px-2 py-1 rounded mt-2 block text-amber-900 font-mono">
                uv run python scripts/generate_datasets.py && uv run python scripts/figures/generate_figure1.py
              </code>
            </div>
            <button
              onClick={() => setGroundTruthModified(false)}
              className="ml-auto text-amber-500 hover:text-amber-700"
            >
              ✕
            </button>
          </div>
        )}

        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Flag Error Analysis
          </h1>
          <p className="text-gray-600">
            {customersWithErrors.length} customers with flag errors{filterMode !== 'all' && ` (filtered from ${allCustomersWithErrors.length})`} • {allProviders.length} providers
          </p>
        </div>

        {/* Filter Bar */}
        <div className="flex justify-center">
          <div className="bg-white border border-gray-200 rounded-lg p-3 flex items-center gap-4 flex-wrap">
            <span className="text-sm font-medium text-gray-700">Filter:</span>
            <div className="inline-flex rounded-lg border border-gray-200 p-1">
              <button
                onClick={() => setFilterMode('all')}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  filterMode === 'all'
                    ? 'bg-blue-100 text-blue-800'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                All ({allCustomersWithErrors.length})
              </button>
              <button
                onClick={() => setFilterMode('undetermined')}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  filterMode === 'undetermined'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Undetermined GT ({allCustomersWithErrors.filter(c => c.hasUndeterminedGroundTruth).length})
              </button>
              <button
                onClick={() => setFilterMode('high_disagreement')}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  filterMode === 'high_disagreement'
                    ? 'bg-red-100 text-red-800'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                High Disagreement
              </button>
            </div>
            {filterMode === 'high_disagreement' && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">≥</span>
                <input
                  type="number"
                  min="1"
                  max="12"
                  value={disagreementThreshold}
                  onChange={(e) => setDisagreementThreshold(Math.max(1, Math.min(12, parseInt(e.target.value) || 1)))}
                  className="w-16 px-2 py-1 border border-gray-300 rounded text-sm"
                />
                <span className="text-sm text-gray-600">providers wrong</span>
              </div>
            )}
          </div>
        </div>

        {/* Mode Toggle */}
        <div className="flex justify-center">
          <div className="inline-flex rounded-lg border border-gray-200 p-1 bg-white">
            <button
              onClick={() => {
                if (currentCustomer.failedProviders.length > 0) {
                  setViewMode('failed');
                  setCurrentProviderIndex(0);
                  setCurrentAssertionIndex(0);
                }
              }}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'failed'
                  ? 'bg-red-100 text-red-800'
                  : 'text-gray-600 hover:text-gray-900'
              } ${currentCustomer.failedProviders.length === 0 ? 'opacity-50 cursor-not-allowed' : ''}`}
              disabled={currentCustomer.failedProviders.length === 0}
            >
              Failed ({currentCustomer.failedProviders.length})
            </button>
            <button
              onClick={() => {
                if (currentCustomer.correctProviders.length > 0) {
                  setViewMode('correct');
                  setCurrentProviderIndex(0);
                  setCurrentAssertionIndex(0);
                }
              }}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'correct'
                  ? 'bg-green-100 text-green-800'
                  : 'text-gray-600 hover:text-gray-900'
              } ${currentCustomer.correctProviders.length === 0 ? 'opacity-50 cursor-not-allowed' : ''}`}
              disabled={currentCustomer.correctProviders.length === 0}
            >
              Correct ({currentCustomer.correctProviders.length})
            </button>
            <button
              onClick={() => {
                setViewMode('all');
                setCurrentProviderIndex(0);
                setCurrentAssertionIndex(0);
              }}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'all'
                  ? 'bg-blue-100 text-blue-800'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              All ({currentCustomer.failedProviders.length + currentCustomer.correctProviders.length})
            </button>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex gap-4 justify-center items-center flex-wrap">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Customer:</label>
            <select
              value={currentCustomerIndex}
              onChange={(e) => {
                const newIdx = Number(e.target.value);
                const newCustomer = customersWithErrors[newIdx];
                const newProviders = getCurrentProviders(newCustomer);
                if (newProviders.length === 0 && viewMode !== 'all') {
                  setViewMode('failed');
                }
                setCurrentCustomerIndex(newIdx);
                setCurrentProviderIndex(0);
                setCurrentAssertionIndex(0);
              }}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 max-w-xs"
            >
              {customersWithErrors.map((customer, idx) => (
                <option key={idx} value={idx}>
                  {idx + 1}. {customer.customerName}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Provider:</label>
            <select
              value={currentProviderIndex}
              onChange={(e) => {
                setCurrentProviderIndex(Number(e.target.value));
                setCurrentAssertionIndex(0);
              }}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {currentProviders.map((pr, idx) => (
                <option key={idx} value={idx}>
                  {pr.provider} {pr.isCorrect ? '✓' : `(${pr.flagErrors.length} errors)`}
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
              {currentProviderResult?.relevantAssertions.map((assertion, idx) => (
                <option key={idx} value={idx}>
                  {assertion.metricName}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Keyboard Navigation Help */}
        <div className="text-center text-sm text-gray-500">
          ↑↓ customers • ←→ assertions • Tab cycle view mode • Space cycle category • Enter comment • <kbd className="px-1 py-0.5 bg-gray-200 rounded text-xs">f</kbd> cycle ground truth
        </div>

        {/* Error Category Display - show when current provider has errors */}
        {currentProviderResult && !currentProviderResult.isCorrect && currentFlagType && (
          <div className="flex justify-center">
            <div className="bg-white border border-gray-200 rounded-lg p-4 flex items-center gap-4">
              <span className="text-sm font-medium text-gray-700">Error Category:</span>
              <div className="flex gap-2">
                {ERROR_CATEGORIES.map((cat, idx) => (
                  <button
                    key={idx}
                    onClick={() => saveRecord({ errorCategory: cat })}
                    className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                      currentRecord?.errorCategory === cat
                        ? cat === null
                          ? 'bg-gray-200 text-gray-800'
                          : 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {cat ? ERROR_CATEGORY_LABELS[cat] : 'None'}
                  </button>
                ))}
              </div>
              {currentRecord?.comment && (
                <Badge variant="outline" className="ml-2 bg-yellow-50 text-yellow-700">
                  Has comment
                </Badge>
              )}
            </div>
          </div>
        )}

        {/* Customer Info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <span>Customer {currentCustomerIndex + 1} of {customersWithErrors.length}</span>
              <Badge variant="outline" className="bg-red-50 text-red-700">
                {currentCustomer.failedProviders.length} failed
              </Badge>
              <Badge variant="outline" className="bg-green-50 text-green-700">
                {currentCustomer.correctProviders.length} correct
              </Badge>
            </CardTitle>
            <CardDescription>
              <div className="mt-2">
                <span className="text-sm whitespace-pre-wrap">
                  {currentCustomer.customerInfo}
                </span>
              </div>
            </CardDescription>
          </CardHeader>
        </Card>

        {/* Provider Agreement Summary */}
        <Card className="border-gray-200 bg-gray-50">
          <CardHeader className="py-3">
            <CardTitle className="text-sm font-medium text-gray-700">Provider Agreement Summary</CardTitle>
          </CardHeader>
          <CardContent className="py-2">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {FLAG_TYPES_ORDER.map(flagType => {
                const counts = currentCustomer.flagAgreement[flagType];
                const total = counts.FLAG + counts['NO FLAG'] + counts.UNDETERMINED;
                const gtFlag = currentCustomer.groundTruthFlags?.[flagType] || 'UNDETERMINED';
                return (
                  <div key={flagType} className="bg-white rounded border border-gray-200 p-2">
                    <div className="font-medium capitalize text-sm text-gray-800 flex items-center justify-between">
                      <span>{flagType}</span>
                      <Badge
                        variant="outline"
                        className={`text-xs ${
                          gtFlag === 'FLAG' ? 'bg-red-50 text-red-700 border-red-200' :
                          gtFlag === 'NO FLAG' ? 'bg-green-50 text-green-700 border-green-200' :
                          'bg-yellow-50 text-yellow-700 border-yellow-200'
                        }`}
                      >
                        GT: {gtFlag}
                      </Badge>
                    </div>
                    <div className="mt-1 text-xs text-gray-600 space-y-0.5">
                      {counts.FLAG > 0 && (
                        <div className="flex justify-between">
                          <span className="text-red-600">FLAG:</span>
                          <span>{counts.FLAG}/{total}</span>
                        </div>
                      )}
                      {counts['NO FLAG'] > 0 && (
                        <div className="flex justify-between">
                          <span className="text-green-600">NO FLAG:</span>
                          <span>{counts['NO FLAG']}/{total}</span>
                        </div>
                      )}
                      {counts.UNDETERMINED > 0 && (
                        <div className="flex justify-between">
                          <span className="text-yellow-600">UNDETERMINED:</span>
                          <span>{counts.UNDETERMINED}/{total}</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Provider & Flag Summary */}
        {currentProviderResult && (
          <Card className={currentProviderResult.isCorrect ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
            <CardHeader>
              <CardTitle className={`flex items-center gap-3 ${currentProviderResult.isCorrect ? 'text-green-800' : 'text-red-800'}`}>
                <span>{currentProviderResult.isCorrect ? 'Correct:' : 'Flag Errors:'} {currentProviderResult.provider}</span>
                <Badge variant="secondary">
                  Provider {currentProviderIndex + 1} of {currentProviders.length}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {currentProviderResult.isCorrect ? (
                <div className="text-green-700 font-medium">
                  All 4 flags match ground truth
                </div>
              ) : (
                <div className="flex flex-wrap gap-4">
                  {currentProviderResult.flagErrors.map((error, idx) => {
                    const errKey = getRecordKey(currentCustomer.customerName, currentProviderResult.provider, error.flagType);
                    const errRecord = savedRecords.get(errKey);
                    return (
                      <div key={idx} className={`bg-white p-3 rounded border ${error.flagType === currentFlagType ? 'border-blue-400 ring-2 ring-blue-200' : 'border-red-200'}`}>
                        <div className="font-semibold capitalize text-red-700 flex items-center gap-2">
                          {error.flagType}
                          {errRecord?.errorCategory && (
                            <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700">
                              {ERROR_CATEGORY_LABELS[errRecord.errorCategory]}
                            </Badge>
                          )}
                        </div>
                        <div className="text-sm mt-1">
                          <span className="text-gray-600">Extracted: </span>
                          <Badge variant={error.extractedFlag === 'FLAG' ? 'destructive' : error.extractedFlag === 'NO FLAG' ? 'default' : 'secondary'}>
                            {error.extractedFlag}
                          </Badge>
                        </div>
                        <div className="text-sm mt-1">
                          <span className="text-gray-600">Ground Truth: </span>
                          <Badge variant={error.groundTruthFlag === 'FLAG' ? 'destructive' : error.groundTruthFlag === 'NO FLAG' ? 'default' : 'secondary'}>
                            {error.groundTruthFlag}
                          </Badge>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Current Assertion */}
        {currentAssertion && (() => {
          const flagType = extractFlagTypeFromMetric(currentAssertion.metricName);
          const liveGT = flagType && currentCustomer.groundTruthFlags
            ? currentCustomer.groundTruthFlags[flagType]
            : undefined;
          const extractedFlag = currentAssertion.extractedFlag ?? 'UNDETERMINED';
          const isCorrect = liveGT ? extractedFlag === liveGT : undefined;
          return (
            <AssertionDetails
              assertion={currentAssertion}
              index={globalAssertionIndex}
              total={totalAssertions}
              removeImagesFromMarkdown={removeImagesFromMarkdown}
              liveGroundTruthFlag={liveGT}
              isCorrectWithLiveGT={isCorrect}
            />
          );
        })()}

        {/* Navigation Footer */}
        <div className="text-center text-sm text-gray-400">
          Customer {currentCustomerIndex + 1} of {customersWithErrors.length} •
          {currentProviderResult?.isCorrect ? ' Correct' : ' Failed'} Provider {currentProviderIndex + 1} of {currentProviders.length} •
          Assertion {globalAssertionIndex + 1} of {totalAssertions}
        </div>
      </div>

      {/* Comment Modal */}
      <CommentModal
        isOpen={commentModalOpen}
        onClose={() => setCommentModalOpen(false)}
        onSubmit={handleSaveComment}
        customerName={currentCustomer?.customerName || ''}
        provider={currentProviderResult?.provider || ''}
        flagType={currentFlagType}
        metricName={currentAssertion?.metricName || ''}
        extractedFlag={currentAssertion?.extractedFlag || 'UNDETERMINED'}
        groundTruthFlag={currentAssertion?.groundTruthFlag || 'UNDETERMINED'}
        existingComment={currentRecord?.comment || null}
      />
    </div>
  );
}
