'use client';

import { Badge } from "@/components/ui/badge";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface SourceAnalysis {
  description: string;
  customerProximity: {
    classification: string;
    justification: string;
  };
  organismProximity: {
    classification: string;
    justification: string;
  };
  laboratoryWork: {
    classification: string;
    justification: string;
  };
  relevanceLevel: number | null;
}

interface ProvidedSourceAnalysis {
  id: string;
  analysis: SourceAnalysis;
  result: 'PASS' | 'FAIL' | null;
}

interface ParsedWorkRelevance {
  orderOrganism: string;
  selectedSources: string;
  referenceSourceAnalysis: SourceAnalysis | null;
  providedSources: ProvidedSourceAnalysis[];
  unparsedContent?: string;
}

function extractTagContent(text: string, tagName: string): string | null {
  const regex = new RegExp(`<${tagName}(?:\\s[^>]*)?>([\\s\\S]*?)<\\/${tagName}>`, 'i');
  const match = text.match(regex);
  return match ? match[1].trim() : null;
}

function extractAllTagsWithId(text: string, tagName: string): Array<{ id: string; content: string }> {
  const regex = new RegExp(`<${tagName}(?:\\s+id="([^"]*)")?\\s*>([\\s\\S]*?)<\\/${tagName}>`, 'gi');
  const results: Array<{ id: string; content: string }> = [];
  let match;
  
  while ((match = regex.exec(text)) !== null) {
    results.push({
      id: match[1] || '',
      content: match[2].trim()
    });
  }
  
  return results;
}

function parseSourceAnalysis(content: string | null): SourceAnalysis | null {
  if (!content) return null;

  const result: SourceAnalysis = {
    description: '',
    customerProximity: { classification: '', justification: '' },
    organismProximity: { classification: '', justification: '' },
    laboratoryWork: { classification: '', justification: '' },
    relevanceLevel: null,
  };

  // Parse Description (matches "- Description: ...")
  const descMatch = content.match(/Description:\s*(.+?)(?=\n-|\n<|$)/s);
  if (descMatch) {
    result.description = descMatch[1].trim();
  }

  // Parse Proximity to Customer (matches "- Proximity to Customer: CLASSIFICATION - justification")
  const customerMatch = content.match(/Proximity to Customer:\s*(\w+)\s*[-–]\s*(.+?)(?=\n-|\n<|$)/s);
  if (customerMatch) {
    result.customerProximity.classification = customerMatch[1].trim();
    result.customerProximity.justification = customerMatch[2].trim();
  }

  // Parse Organism Proximity to Order (matches "- Organism Proximity to Order: CLASSIFICATION - justification")
  const orgMatch = content.match(/Organism Proximity(?:\s+to\s+Order)?:\s*(\w+)\s*[-–]\s*(.+?)(?=\n-|\n<|$)/s);
  if (orgMatch) {
    result.organismProximity.classification = orgMatch[1].trim();
    result.organismProximity.justification = orgMatch[2].trim();
  }

  // Parse Laboratory Work Involvement (matches "- Laboratory Work Involvement: CLASSIFICATION - justification")
  const labMatch = content.match(/Laboratory Work(?:\s+Involvement)?:\s*(\w+)\s*[-–]\s*(.+?)(?=\n-|\n<|$)/s);
  if (labMatch) {
    result.laboratoryWork.classification = labMatch[1].trim();
    result.laboratoryWork.justification = labMatch[2].trim();
  }

  // Parse Relevance Level (matches "- Relevance Level: 5" or similar)
  const levelMatch = content.match(/Relevance Level:\s*(\d+)/);
  if (levelMatch) {
    result.relevanceLevel = parseInt(levelMatch[1], 10);
  }

  return result;
}

function parseSourceResult(content: string): 'PASS' | 'FAIL' | null {
  // Match "- Source Result: PASS" or "- Source Result: FAIL" patterns
  const resultMatch = content.match(/Source Result:\s*(PASS|FAIL)/i);
  if (resultMatch) {
    return resultMatch[1].toUpperCase() as 'PASS' | 'FAIL';
  }
  // Also try matching just "- Result:" for backwards compatibility
  const altMatch = content.match(/Result:\s*(PASS|FAIL)/i);
  if (altMatch) {
    return altMatch[1].toUpperCase() as 'PASS' | 'FAIL';
  }
  return null;
}

export function parseWorkRelevanceReason(reason: string): ParsedWorkRelevance {
  const orderOrganism = extractTagContent(reason, 'order_organism') || '';
  const selectedSources = extractTagContent(reason, 'selected_sources') || '';
  const referenceContent = extractTagContent(reason, 'reference_source_analysis');
  
  // Extract all provided_source_analysis blocks with their ids
  const providedBlocks = extractAllTagsWithId(reason, 'provided_source_analysis');
  
  const providedSources: ProvidedSourceAnalysis[] = providedBlocks.map(block => {
    const analysis = parseSourceAnalysis(block.content);
    const result = parseSourceResult(block.content);
    
    return {
      id: block.id,
      analysis: analysis || {
        description: '',
        customerProximity: { classification: '', justification: '' },
        organismProximity: { classification: '', justification: '' },
        laboratoryWork: { classification: '', justification: '' },
        relevanceLevel: null,
      },
      result,
    };
  });

  // Check if we have any structured content
  const hasStructuredContent = orderOrganism || referenceContent || providedSources.length > 0;

  return {
    orderOrganism,
    selectedSources,
    referenceSourceAnalysis: parseSourceAnalysis(referenceContent),
    providedSources,
    unparsedContent: hasStructuredContent ? undefined : reason,
  };
}

function ClassificationBadge({ classification, type }: { classification: string; type: 'proximity' | 'lab' | 'organism' }) {
  const getVariant = (): 'default' | 'secondary' | 'outline' | 'destructive' => {
    const upper = classification.toUpperCase();
    
    if (type === 'proximity') {
      if (upper.includes('CUSTOMER_DIRECT')) return 'default';
      if (upper.includes('INSTITUTION_ONLY')) return 'secondary';
      return 'outline';
    }
    
    if (type === 'lab') {
      if (upper.includes('WET_LAB')) return 'default';
      if (upper.includes('COMPUTATIONAL')) return 'secondary';
      return 'outline';
    }
    
    if (type === 'organism') {
      if (upper.includes('SAME_ORGANISM')) return 'default';
      if (upper.includes('CLOSELY_RELATED')) return 'secondary';
      if (upper.includes('DISTANTLY_RELATED')) return 'outline';
      return 'outline';
    }
    
    return 'outline';
  };

  return (
    <Badge variant={getVariant()} className="font-mono text-xs">
      {classification}
    </Badge>
  );
}

interface SourceAnalysisCardProps {
  title: string;
  analysis: SourceAnalysis;
  type: 'reference' | 'provided';
  result?: 'PASS' | 'FAIL' | null;
}

function SourceAnalysisCard({ title, analysis, type, result }: SourceAnalysisCardProps) {
  const borderColor = type === 'reference' ? 'border-l-amber-500' : 'border-l-blue-500';
  const headerBg = type === 'reference' ? 'bg-amber-50' : 'bg-blue-50';
  const headerText = type === 'reference' ? 'text-amber-800' : 'text-blue-800';

  return (
    <div className={`border rounded-lg overflow-hidden border-l-4 ${borderColor}`}>
      <div className={`px-4 py-2 ${headerBg} flex items-center justify-between`}>
        <h5 className={`font-semibold text-sm ${headerText}`}>{title}</h5>
        <div className="flex items-center gap-2">
          {analysis.relevanceLevel !== null && (
            <Badge variant="outline" className="text-xs font-mono">
              Level {analysis.relevanceLevel}
            </Badge>
          )}
          {result && (
            <Badge variant={result === 'PASS' ? 'default' : 'destructive'} className="text-xs">
              {result}
            </Badge>
          )}
        </div>
      </div>
      <div className="p-4 space-y-4 text-sm">
        {analysis.description && (
          <div>
            <span className="font-medium text-gray-600">Description: </span>
            <span className="text-gray-800">{analysis.description}</span>
          </div>
        )}
        
        <div className="grid gap-3">
          {analysis.customerProximity.classification && (
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-600 text-xs uppercase tracking-wide">Customer Proximity</span>
                <ClassificationBadge classification={analysis.customerProximity.classification} type="proximity" />
              </div>
              {analysis.customerProximity.justification && (
                <p className="text-gray-600 text-xs pl-0">{analysis.customerProximity.justification}</p>
              )}
            </div>
          )}
          
          {analysis.organismProximity.classification && (
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-600 text-xs uppercase tracking-wide">Organism Proximity</span>
                <ClassificationBadge classification={analysis.organismProximity.classification} type="organism" />
              </div>
              {analysis.organismProximity.justification && (
                <p className="text-gray-600 text-xs pl-0">{analysis.organismProximity.justification}</p>
              )}
            </div>
          )}
          
          {analysis.laboratoryWork.classification && (
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-600 text-xs uppercase tracking-wide">Laboratory Work</span>
                <ClassificationBadge classification={analysis.laboratoryWork.classification} type="lab" />
              </div>
              {analysis.laboratoryWork.justification && (
                <p className="text-gray-600 text-xs pl-0">{analysis.laboratoryWork.justification}</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface WorkRelevanceDisplayProps {
  reason: string;
  workUrl?: string | null;
  passingSourceUrl?: string | null;
  extractedAiResponse?: string;
}

export function WorkRelevanceDisplay({ reason, workUrl, passingSourceUrl, extractedAiResponse }: WorkRelevanceDisplayProps) {
  const parsed = parseWorkRelevanceReason(reason);

  // If we couldn't parse structured content, fall back to showing unparsed
  if (parsed.unparsedContent) {
    return (
      <div className="text-sm text-gray-700 whitespace-pre-wrap">
        {parsed.unparsedContent}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Source Links Section */}
      {(workUrl || passingSourceUrl) && (
        <div className="border rounded-lg overflow-hidden">
          <div className="bg-gray-50 px-4 py-2 border-b">
            <h5 className="font-semibold text-sm text-gray-700">Source Comparison</h5>
          </div>
          <div className="p-4 space-y-3">
            {/* Reference Work URL */}
            {workUrl && (
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-amber-700 bg-amber-100 px-2 py-0.5 rounded w-24 text-center flex-shrink-0">
                  Reference
                </span>
                <a 
                  href={workUrl} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-sm text-gray-700 hover:text-blue-600 underline truncate"
                >
                  {workUrl}
                </a>
              </div>
            )}
            {/* Passing Source URL */}
            {passingSourceUrl && (
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-green-700 bg-green-100 px-2 py-0.5 rounded w-24 text-center flex-shrink-0">
                  Passed ✓
                </span>
                <a 
                  href={passingSourceUrl} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-sm text-green-700 hover:text-green-900 underline truncate"
                >
                  {passingSourceUrl}
                </a>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Order Organism */}
      {parsed.orderOrganism && (
        <div className="bg-gradient-to-r from-violet-50 to-purple-50 border border-violet-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-8 h-8 bg-violet-100 rounded-full flex items-center justify-center">
              <svg className="w-4 h-4 text-violet-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
            </div>
            <div>
              <h4 className="font-semibold text-violet-800 text-sm mb-1">Ordered Organism/Sequence</h4>
              <p className="text-violet-700 text-sm">{parsed.orderOrganism}</p>
            </div>
          </div>
        </div>
      )}

      {/* Selected Sources */}
      {parsed.selectedSources && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-700 text-sm mb-2">Selected Sources (Highest Relevance Level)</h4>
          <p className="text-gray-600 text-sm whitespace-pre-wrap">{parsed.selectedSources}</p>
        </div>
      )}

      {/* Reference Source Card */}
      {parsed.referenceSourceAnalysis && (
        <div>
          <h4 className="font-semibold text-gray-700 text-sm mb-3">Reference Source</h4>
          <SourceAnalysisCard 
            title="Reference Source" 
            analysis={parsed.referenceSourceAnalysis} 
            type="reference" 
          />
        </div>
      )}

      {/* Provided Source Cards - Multiple */}
      {parsed.providedSources.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-700 text-sm mb-3">
            Provided Sources ({parsed.providedSources.length})
          </h4>
          <div className="space-y-4">
            {parsed.providedSources.map((source, idx) => (
              <SourceAnalysisCard 
                key={idx}
                title={source.id || `Provided Source ${idx + 1}`}
                analysis={source.analysis} 
                type="provided"
                result={source.result}
              />
            ))}
          </div>
        </div>
      )}

      {/* Extracted AI Response */}
      {extractedAiResponse && (
        <div className="border rounded-lg overflow-hidden">
          <div className="bg-slate-50 px-4 py-2 border-b">
            <h5 className="font-semibold text-sm text-slate-700">AI Response (Source of Links)</h5>
          </div>
          <div className="p-4 max-h-64 overflow-y-auto">
            <div className="markdown text-sm">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {extractedAiResponse}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}













