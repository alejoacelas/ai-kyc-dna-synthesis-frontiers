import { Badge } from "@/components/ui/badge";

type FlagValue = 'FLAG' | 'NO FLAG' | 'UNDETERMINED';

interface FlagAccuracyDisplayProps {
  extractedFlag: FlagValue;
  groundTruthFlag: FlagValue;
  reason: string;
  claimType: string;
}

const getFlagBadgeVariant = (flag: FlagValue): 'default' | 'destructive' | 'secondary' | 'outline' => {
  switch (flag) {
    case 'FLAG':
      return 'destructive';
    case 'NO FLAG':
      return 'default';
    case 'UNDETERMINED':
      return 'secondary';
    default:
      return 'outline';
  }
};

const getFlagBadgeClass = (flag: FlagValue): string => {
  switch (flag) {
    case 'FLAG':
      return 'bg-red-100 text-red-800 border-red-300';
    case 'NO FLAG':
      return 'bg-green-100 text-green-800 border-green-300';
    case 'UNDETERMINED':
      return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    default:
      return '';
  }
};

export function FlagAccuracyDisplay({
  extractedFlag,
  groundTruthFlag,
  reason,
  claimType,
}: FlagAccuracyDisplayProps) {
  const isMatch = extractedFlag === groundTruthFlag || groundTruthFlag === 'UNDETERMINED' || extractedFlag === 'UNDETERMINED';
  
  return (
    <div className="space-y-4">
      {/* Flag Comparison */}
      <div className="flex items-center gap-6">
        <div className="flex flex-col items-center">
          <span className="text-xs text-gray-500 mb-1">AI Output</span>
          <Badge 
            variant="outline" 
            className={`${getFlagBadgeClass(extractedFlag)} text-sm px-3 py-1`}
          >
            {extractedFlag}
          </Badge>
        </div>
        
        <div className="flex items-center">
          <span className={`text-2xl ${isMatch ? 'text-green-500' : 'text-red-500'}`}>
            {isMatch ? '=' : '≠'}
          </span>
        </div>
        
        <div className="flex flex-col items-center">
          <span className="text-xs text-gray-500 mb-1">Ground Truth</span>
          <Badge 
            variant="outline" 
            className={`${getFlagBadgeClass(groundTruthFlag)} text-sm px-3 py-1`}
          >
            {groundTruthFlag}
          </Badge>
        </div>
      </div>

      {/* Reason */}
      <div className="text-sm text-gray-700 bg-gray-50 rounded p-3">
        {reason}
      </div>

      {/* Keyboard hint */}
      <div className="text-xs text-gray-400 flex items-center gap-1">
        <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-300 rounded text-xs font-mono">f</kbd>
        <span>to cycle ground truth: FLAG → NO FLAG → UNDETERMINED</span>
      </div>
    </div>
  );
}









