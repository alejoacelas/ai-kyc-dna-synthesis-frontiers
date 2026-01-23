import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const DATA_DIR = path.join(process.cwd(), '..', 'data');
const COMMENTS_FILE = path.join(DATA_DIR, 'annotations', 'flag_error_comments.json');

type FlagValue = 'FLAG' | 'NO FLAG' | 'UNDETERMINED';
type FlagType = 'affiliation' | 'institution' | 'domain' | 'sanctions';
type ErrorCategory = 'empty_response' | 'information_not_found' | 'flag_instructions_not_followed' | 'difference_in_judgment' | 'factual_mistake' | null;

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
  extractedModelResponse: string | null; // The extracted section from source-reliability/claim-support
}

interface CommentsData {
  version: string;
  created: string;
  lastUpdated: string;
  records: FlagErrorRecord[];
}

function ensureCommentsFile(): CommentsData {
  const annotationsDir = path.join(DATA_DIR, 'annotations');
  if (!fs.existsSync(annotationsDir)) {
    fs.mkdirSync(annotationsDir, { recursive: true });
  }

  if (!fs.existsSync(COMMENTS_FILE)) {
    const defaultData: CommentsData = {
      version: '1.1',
      created: new Date().toISOString(),
      lastUpdated: new Date().toISOString(),
      records: []
    };
    fs.writeFileSync(COMMENTS_FILE, JSON.stringify(defaultData, null, 2), 'utf8');
    return defaultData;
  }

  const data = JSON.parse(fs.readFileSync(COMMENTS_FILE, 'utf8'));

  // Migrate old format (comments array) to new format (records array)
  if (data.comments && !data.records) {
    data.records = data.comments.map((c: any) => ({
      ...c,
      lastUpdated: c.timestamp,
      errorCategory: c.errorCategory || null,
      extractedModelResponse: c.extractedModelResponse || null,
    }));
    delete data.comments;
    data.version = '1.1';
    fs.writeFileSync(COMMENTS_FILE, JSON.stringify(data, null, 2), 'utf8');
  }

  return data;
}

// Generate a unique key for a record based on customer, provider, and flag type
function getRecordKey(customerName: string, provider: string, flagType: string): string {
  return `${customerName}|${provider}|${flagType}`;
}

export async function GET() {
  try {
    const data = ensureCommentsFile();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error reading flag_error_comments.json:', error);
    return NextResponse.json({ error: 'Failed to load comments' }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const {
      customerName,
      customerInfoPreview,
      provider,
      flagType,
      extractedFlag,
      groundTruthFlag,
      metricName,
      comment,
      errorCategory,
      isCorrectProvider,
      extractedModelResponse,
    } = body as Partial<FlagErrorRecord>;

    // Validate required fields
    if (!customerName || !provider || !flagType) {
      return NextResponse.json(
        { error: 'Missing required fields: customerName, provider, flagType' },
        { status: 400 }
      );
    }

    const data = ensureCommentsFile();
    const recordKey = getRecordKey(customerName, provider, flagType);

    // Find existing record or create new one
    const existingIndex = data.records.findIndex(
      r => getRecordKey(r.customerName, r.provider, r.flagType) === recordKey
    );

    const now = new Date().toISOString();

    if (existingIndex >= 0) {
      // Update existing record
      const existing = data.records[existingIndex];
      data.records[existingIndex] = {
        ...existing,
        lastUpdated: now,
        // Only update fields that are provided
        ...(comment !== undefined && { comment }),
        ...(errorCategory !== undefined && { errorCategory }),
        ...(extractedModelResponse !== undefined && { extractedModelResponse }),
        ...(metricName !== undefined && { metricName }),
        ...(extractedFlag !== undefined && { extractedFlag }),
        ...(groundTruthFlag !== undefined && { groundTruthFlag }),
        ...(customerInfoPreview !== undefined && { customerInfoPreview }),
        ...(isCorrectProvider !== undefined && { isCorrectProvider }),
      };
    } else {
      // Create new record
      const newRecord: FlagErrorRecord = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: now,
        lastUpdated: now,
        customerName,
        customerInfoPreview: customerInfoPreview || '',
        provider,
        flagType: flagType as FlagType | 'unknown',
        extractedFlag: extractedFlag || 'UNDETERMINED',
        groundTruthFlag: groundTruthFlag || 'UNDETERMINED',
        metricName: metricName || '',
        comment: comment || null,
        errorCategory: errorCategory || null,
        isCorrectProvider: isCorrectProvider || false,
        extractedModelResponse: extractedModelResponse || null,
      };
      data.records.push(newRecord);
    }

    data.lastUpdated = now;
    fs.writeFileSync(COMMENTS_FILE, JSON.stringify(data, null, 2), 'utf8');

    const savedRecord = existingIndex >= 0
      ? data.records[existingIndex]
      : data.records[data.records.length - 1];

    return NextResponse.json({
      success: true,
      record: savedRecord,
    });
  } catch (error) {
    console.error('Error saving record:', error);
    return NextResponse.json({ error: 'Failed to save record' }, { status: 500 });
  }
}
