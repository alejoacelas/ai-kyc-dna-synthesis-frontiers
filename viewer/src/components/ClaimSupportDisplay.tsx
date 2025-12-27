'use client';

import { memo } from 'react';
import { Badge } from "@/components/ui/badge";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export interface Claim {
  number: number;
  // New format fields
  assertion: string;
  status: string;
  note: string;
  // Legacy fields for backward compatibility
  whatIsClaimed?: string;
  reasoning?: string;
  verdict?: string;
  isSupported: boolean;
}

interface ClaimSupportDisplayProps {
  reason: string;
  claims?: Claim[];
}

const getStatusBadgeVariant = (status: string): 'default' | 'destructive' | 'secondary' | 'outline' => {
  const upperStatus = status.toUpperCase();
  // Handle new format (PASS/FAIL)
  if (upperStatus === 'PASS') return 'default';
  if (upperStatus === 'FAIL') return 'destructive';
  // Handle legacy format
  if (upperStatus === 'SUPPORTED' || upperStatus === 'GENERAL_KNOWLEDGE') return 'default';
  if (upperStatus === 'UNSOURCED' || upperStatus === 'MISREPRESENTED') return 'destructive';
  return 'outline';
};

const getStatusColor = (status: string): string => {
  const upperStatus = status.toUpperCase();
  // Handle new format (PASS/FAIL)
  if (upperStatus === 'PASS') return 'text-green-700 bg-green-50 border-green-200';
  if (upperStatus === 'FAIL') return 'text-red-700 bg-red-50 border-red-200';
  // Handle legacy format
  if (upperStatus === 'SUPPORTED') return 'text-green-700 bg-green-50 border-green-200';
  if (upperStatus === 'GENERAL_KNOWLEDGE') return 'text-blue-700 bg-blue-50 border-blue-200';
  if (upperStatus === 'UNSOURCED') return 'text-red-700 bg-red-50 border-red-200';
  if (upperStatus === 'MISREPRESENTED') return 'text-orange-700 bg-orange-50 border-orange-200';
  return 'text-gray-700 bg-gray-50 border-gray-200';
};

const ClaimCard = memo(function ClaimCard({ claim }: { claim: Claim }) {
  const displayStatus = claim.status || claim.verdict || 'UNKNOWN';
  const displayAssertion = claim.assertion || claim.whatIsClaimed || '';
  const displayNote = claim.note || claim.reasoning || '';

  return (
    <div className={`border rounded-lg p-4 ${getStatusColor(displayStatus)}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">Claim {claim.number}</span>
        <Badge variant={getStatusBadgeVariant(displayStatus)}>
          {displayStatus}
        </Badge>
      </div>
      
      <div className="space-y-2">
        <div>
          <span className="text-xs font-medium uppercase text-gray-500">Assertion:</span>
          <p className="text-sm mt-1">{displayAssertion}</p>
        </div>
        
        {displayNote && (
          <div>
            <span className="text-xs font-medium uppercase text-gray-500">Note:</span>
            <p className="text-sm mt-1">{displayNote}</p>
          </div>
        )}
      </div>
    </div>
  );
});

export const ClaimSupportDisplay = memo(function ClaimSupportDisplay({
  reason,
  claims,
}: ClaimSupportDisplayProps) {
  // If no claims parsed, fall back to displaying reason as markdown (backward compatible)
  if (!claims || claims.length === 0) {
    return (
      <div className="markdown">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {reason}
        </ReactMarkdown>
      </div>
    );
  }

  // Count statuses for summary (handles both new PASS/FAIL and legacy formats)
  const passing = claims.filter(c => {
    const status = (c.status || c.verdict || '').toUpperCase();
    return status === 'PASS' || status === 'SUPPORTED' || status === 'GENERAL_KNOWLEDGE';
  }).length;
  const failing = claims.filter(c => {
    const status = (c.status || c.verdict || '').toUpperCase();
    return status === 'FAIL' || status === 'UNSOURCED' || status === 'MISREPRESENTED';
  }).length;

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="flex flex-wrap gap-2 items-center">
        <span className="text-sm font-medium text-gray-600">Claims Summary:</span>
        {passing > 0 && (
          <Badge variant="default" className="bg-green-600">
            {passing} Pass
          </Badge>
        )}
        {failing > 0 && (
          <Badge variant="destructive">
            {failing} Fail
          </Badge>
        )}
      </div>

      {/* Individual claims */}
      <div className="space-y-3">
        {claims.map((claim) => (
          <ClaimCard key={claim.number} claim={claim} />
        ))}
      </div>
    </div>
  );
});

export default ClaimSupportDisplay;

