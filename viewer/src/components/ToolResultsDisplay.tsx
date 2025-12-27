'use client';

import { memo, useState } from 'react';
import { Badge } from "@/components/ui/badge";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// Tool result types based on the data structure
interface WebResult {
  url: string;
  title: string;
  content: string;
}

interface EpmcMatchingAuthor {
  first_name: string;
  last_name: string;
  affiliations: string[];
  orcid?: string;
}

interface EpmcResult {
  title: string;
  author_string: string;
  matching_authors: EpmcMatchingAuthor[];
}

interface OrcidEducation {
  organization: string;
  department: string;
  role: string;
  city: string;
  country: string;
  start_date: string | null;
  end_date: string | null;
}

interface OrcidWork {
  title: string;
  type: string;
  publication_date: string;
  journal: string;
  url: string;
  identifiers: Array<{
    type: string;
    value: string;
  }>;
}

interface OrcidResult {
  orcid_id: string;
  orcid_url: string;
  given_name: string;
  family_name: string;
  credit_name: string | null;
  biography: string | null;
  keywords: string[];
  emails: string[];
  external_ids: unknown[];
  urls: unknown[];
  education: OrcidEducation[];
  employment: unknown[];
  total_works_count: number;
  works: OrcidWork[];
}

interface ScreenResult {
  name: string;
  programs: string[];
  source: string;
}

export interface ToolResult {
  id: string;
  result: WebResult | EpmcResult | OrcidResult | ScreenResult | Record<string, unknown>;
  found?: boolean;
}

interface ToolResultsDisplayProps {
  toolResults: ToolResult[];
  removeImagesFromMarkdown?: (markdown: string) => string;
}

const defaultRemoveImages = (markdown: string): string => {
  return markdown.replace(/!\[.*?\]\(.*?\)/g, '');
};

// Type guards
const isWebResult = (result: unknown): result is WebResult => {
  return (
    typeof result === 'object' &&
    result !== null &&
    'url' in result &&
    'content' in result
  );
};

const isEpmcResult = (result: unknown): result is EpmcResult => {
  return (
    typeof result === 'object' &&
    result !== null &&
    'author_string' in result &&
    'matching_authors' in result
  );
};

const isOrcidResult = (result: unknown): result is OrcidResult => {
  return (
    typeof result === 'object' &&
    result !== null &&
    'orcid_id' in result &&
    'orcid_url' in result
  );
};

const isScreenResult = (result: unknown): result is ScreenResult => {
  return (
    typeof result === 'object' &&
    result !== null &&
    'programs' in result &&
    'source' in result &&
    Array.isArray((result as ScreenResult).programs)
  );
};

// Individual result type components
const WebResultDisplay = memo(function WebResultDisplay({
  result,
  removeImagesFromMarkdown,
}: {
  result: WebResult;
  removeImagesFromMarkdown: (markdown: string) => string;
}) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <a
          href={result.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline font-medium text-sm"
        >
          {result.title || result.url}
        </a>
      </div>
      <p className="text-xs text-gray-500 truncate">{result.url}</p>
      {result.content && (
        <div>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-xs text-blue-500 hover:underline mb-2"
          >
            {isExpanded ? '▼ Hide content' : '▶ Show content'}
          </button>
          {isExpanded && (
            <div className="border rounded max-h-96 overflow-y-auto p-3 bg-gray-50">
              <div className="markdown text-sm prose prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {removeImagesFromMarkdown(result.content)}
                </ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
});

const EpmcResultDisplay = memo(function EpmcResultDisplay({
  result,
  found,
}: {
  result: EpmcResult;
  found?: boolean;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Badge variant={found !== false ? 'default' : 'secondary'} className="text-xs">
          {found !== false ? 'Found' : 'Not Found'}
        </Badge>
      </div>
      <p className="font-medium text-sm">{result.title}</p>
      <p className="text-xs text-gray-600">Authors: {result.author_string}</p>
      {Array.isArray(result.matching_authors) && result.matching_authors.length > 0 && (
        <div className="pl-4 border-l-2 border-gray-200">
          <p className="text-xs font-medium text-gray-700">Matching Authors:</p>
          {result.matching_authors.map((author, idx) => (
            <div key={idx} className="text-xs text-gray-600 mt-1">
              <span className="font-medium">{author.first_name} {author.last_name}</span>
              {author.orcid && (
                <span className="ml-2 text-gray-500">ORCID: {author.orcid}</span>
              )}
              {Array.isArray(author.affiliations) && author.affiliations.length > 0 && (
                <ul className="ml-4 list-disc">
                  {author.affiliations.map((aff, affIdx) => (
                    <li key={affIdx}>{aff}</li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
});

const OrcidResultDisplay = memo(function OrcidResultDisplay({
  result,
}: {
  result: OrcidResult;
}) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <a
          href={result.orcid_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline font-medium text-sm"
        >
          {result.given_name} {result.family_name}
        </a>
        <span className="text-xs text-gray-500">({result.orcid_id})</span>
      </div>
      {Array.isArray(result.emails) && result.emails.length > 0 && (
        <p className="text-xs text-gray-600">
          Email: {result.emails.join(', ')}
        </p>
      )}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="text-xs text-blue-500 hover:underline"
      >
        {isExpanded ? '▼ Hide details' : '▶ Show details'}
      </button>
      {isExpanded && (
        <div className="space-y-3 pl-4 border-l-2 border-gray-200">
          {Array.isArray(result.education) && result.education.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-700">Education:</p>
              {result.education.map((edu, idx) => (
                <div key={idx} className="text-xs text-gray-600 mt-1">
                  <span className="font-medium">{edu.role}</span> - {edu.organization}
                  {edu.department && ` (${edu.department})`}
                  <span className="text-gray-500 ml-1">
                    {edu.city}, {edu.country}
                  </span>
                  {edu.start_date && (
                    <span className="text-gray-400 ml-1">
                      ({edu.start_date} - {edu.end_date || 'present'})
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
          {Array.isArray(result.works) && result.works.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-700">
                Works ({result.total_works_count} total, showing {result.works.length}):
              </p>
              {result.works.slice(0, 5).map((work, idx) => (
                <div key={idx} className="text-xs text-gray-600 mt-1">
                  <a
                    href={work.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    {work.title}
                  </a>
                  <span className="text-gray-500 ml-1">
                    ({work.publication_date}) - {work.journal}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
});

const ScreenResultDisplay = memo(function ScreenResultDisplay({
  result,
}: {
  result: ScreenResult;
}) {
  return (
    <div className="space-y-1">
      <p className="font-medium text-sm">{result.name}</p>
      <div className="flex flex-wrap gap-1">
        {result.programs.map((program, idx) => (
          <Badge key={idx} variant="destructive" className="text-xs">
            {program}
          </Badge>
        ))}
      </div>
      <p className="text-xs text-gray-500">Source: {result.source}</p>
    </div>
  );
});

const GenericResultDisplay = memo(function GenericResultDisplay({
  result,
}: {
  result: Record<string, unknown>;
}) {
  return (
    <pre className="text-xs bg-gray-50 p-2 rounded overflow-x-auto max-h-48">
      {JSON.stringify(result, null, 2)}
    </pre>
  );
});

// Main component
export const ToolResultsDisplay = memo(function ToolResultsDisplay({
  toolResults,
  removeImagesFromMarkdown = defaultRemoveImages,
}: ToolResultsDisplayProps) {
  if (!toolResults || toolResults.length === 0) {
    return null;
  }

  // Group results by type
  const webResults = toolResults.filter(tr => tr.id.startsWith('web'));
  const epmcResults = toolResults.filter(tr => tr.id.startsWith('epmc'));
  const orcidResults = toolResults.filter(tr => tr.id.startsWith('orcid'));
  const screenResults = toolResults.filter(tr => tr.id.startsWith('screen'));
  const otherResults = toolResults.filter(
    tr =>
      !tr.id.startsWith('web') &&
      !tr.id.startsWith('epmc') &&
      !tr.id.startsWith('orcid') &&
      !tr.id.startsWith('screen')
  );

  const getToolTypeLabel = (id: string): string => {
    if (id.startsWith('web')) return 'Web Source';
    if (id.startsWith('epmc')) return 'EPMC Publication';
    if (id.startsWith('orcid')) return 'ORCID Profile';
    if (id.startsWith('screen')) return 'Screening Match';
    return 'Tool Result';
  };

  const getToolTypeBadgeVariant = (id: string): 'default' | 'secondary' | 'outline' | 'destructive' => {
    if (id.startsWith('web')) return 'outline';
    if (id.startsWith('epmc')) return 'secondary';
    if (id.startsWith('orcid')) return 'default';
    if (id.startsWith('screen')) return 'destructive';
    return 'outline';
  };

  const renderToolResult = (toolResult: ToolResult) => {
    const { id, result, found } = toolResult;

    if (id.startsWith('web') && isWebResult(result)) {
      return <WebResultDisplay result={result} removeImagesFromMarkdown={removeImagesFromMarkdown} />;
    }
    if (id.startsWith('epmc') && isEpmcResult(result)) {
      return <EpmcResultDisplay result={result} found={found} />;
    }
    if (id.startsWith('orcid') && isOrcidResult(result)) {
      return <OrcidResultDisplay result={result} />;
    }
    if (id.startsWith('screen') && isScreenResult(result)) {
      return <ScreenResultDisplay result={result} />;
    }
    return <GenericResultDisplay result={result as Record<string, unknown>} />;
  };

  const renderSection = (
    title: string,
    results: ToolResult[],
    icon: string
  ) => {
    if (results.length === 0) return null;

    return (
      <div className="space-y-3">
        <h5 className="text-sm font-medium text-gray-700 flex items-center gap-2">
          <span>{icon}</span>
          {title} ({results.length})
        </h5>
        <div className="space-y-4">
          {results.map((toolResult) => (
            <div
              key={toolResult.id}
              className="border rounded-lg p-4 bg-white shadow-sm"
            >
              <div className="flex items-center gap-2 mb-2">
                <Badge variant={getToolTypeBadgeVariant(toolResult.id)} className="text-xs">
                  {toolResult.id}
                </Badge>
                <span className="text-xs text-gray-500">
                  {getToolTypeLabel(toolResult.id)}
                </span>
              </div>
              {renderToolResult(toolResult)}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {renderSection('EPMC Publications', epmcResults, '📚')}
      {renderSection('ORCID Profiles', orcidResults, '👤')}
      {renderSection('Screening Results', screenResults, '🔍')}
      {renderSection('Web Sources', webResults, '🌐')}
      {renderSection('Other Results', otherResults, '📋')}
    </div>
  );
});

export default ToolResultsDisplay;













