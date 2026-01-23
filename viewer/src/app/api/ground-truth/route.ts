import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';

// Data directory: analysis/data (relative to viewer/)
const DATA_DIR = path.join(process.cwd(), '..', 'data');
const GROUND_TRUTH_FILE = path.join(DATA_DIR, 'annotations', 'ground_truth_flags.json');

type FlagValue = 'FLAG' | 'NO FLAG' | 'UNDETERMINED';
type FlagType = 'affiliation' | 'institution' | 'domain' | 'sanctions';

interface GroundTruthRecord {
  customerInfoPreview: string;
  flags: {
    affiliation: FlagValue;
    institution: FlagValue;
    domain: FlagValue;
    sanctions: FlagValue;
  };
  notes: string;
  lastReviewed: string | null;
}

interface GroundTruthData {
  version: string;
  created: string;
  lastUpdated: string;
  records: Record<string, GroundTruthRecord>;
}

function getRecordKey(customerInfo: string): string {
  const normalized = customerInfo.toLowerCase().replace(/\s+/g, ' ').trim();
  return crypto.createHash('sha256').update(normalized).digest('hex').substring(0, 16);
}

function ensureGroundTruthFile(): GroundTruthData {
  if (!fs.existsSync(GROUND_TRUTH_FILE)) {
    const defaultData: GroundTruthData = {
      version: '1.0',
      created: new Date().toISOString(),
      lastUpdated: new Date().toISOString(),
      records: {}
    };
    fs.writeFileSync(GROUND_TRUTH_FILE, JSON.stringify(defaultData, null, 2), 'utf8');
    return defaultData;
  }
  return JSON.parse(fs.readFileSync(GROUND_TRUTH_FILE, 'utf8'));
}

export async function GET() {
  try {
    const data = ensureGroundTruthFile();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error reading ground_truth_flags.json:', error);
    return NextResponse.json({ error: 'Failed to load ground truth' }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { recordKey, customerInfo, flagType, value } = body as {
      recordKey?: string;
      customerInfo?: string;
      flagType: FlagType;
      value: FlagValue;
    };

    // Validate inputs
    const validFlagTypes: FlagType[] = ['affiliation', 'institution', 'domain', 'sanctions'];
    const validValues: FlagValue[] = ['FLAG', 'NO FLAG', 'UNDETERMINED'];

    if (!validFlagTypes.includes(flagType)) {
      return NextResponse.json({ error: `Invalid flag type: ${flagType}` }, { status: 400 });
    }

    if (!validValues.includes(value)) {
      return NextResponse.json({ error: `Invalid value: ${value}` }, { status: 400 });
    }

    // Get record key either directly or by computing from customerInfo
    let key = recordKey;
    if (!key && customerInfo) {
      key = getRecordKey(customerInfo);
    }

    if (!key) {
      return NextResponse.json({ error: 'Either recordKey or customerInfo is required' }, { status: 400 });
    }

    // Read existing data
    const data = ensureGroundTruthFile();

    // Check if record exists
    if (!data.records[key]) {
      // Create new record if customerInfo is provided
      if (customerInfo) {
        data.records[key] = {
          customerInfoPreview: customerInfo.substring(0, 100) + (customerInfo.length > 100 ? '...' : ''),
          flags: {
            affiliation: 'UNDETERMINED',
            institution: 'UNDETERMINED',
            domain: 'UNDETERMINED',
            sanctions: 'UNDETERMINED'
          },
          notes: '',
          lastReviewed: null
        };
      } else {
        return NextResponse.json({ error: `Record not found: ${key}` }, { status: 404 });
      }
    }

    // Update the specific flag
    data.records[key].flags[flagType] = value;
    data.records[key].lastReviewed = new Date().toISOString();
    data.lastUpdated = new Date().toISOString();

    // Write back to file
    fs.writeFileSync(GROUND_TRUTH_FILE, JSON.stringify(data, null, 2), 'utf8');

    return NextResponse.json({ 
      success: true, 
      recordKey: key,
      updatedFlags: data.records[key].flags 
    });
  } catch (error) {
    console.error('Error saving ground truth:', error);
    return NextResponse.json({ error: 'Failed to save ground truth' }, { status: 500 });
  }
}









