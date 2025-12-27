import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// Data directory: analysis/data (relative to viewer/)
const DATA_DIR = path.join(process.cwd(), '..', 'data');
const AGREEMENTS_FILE = path.join(DATA_DIR, 'agreements.json');

// Ensure the file exists with empty array if it doesn't
function ensureAgreementsFile() {
  if (!fs.existsSync(AGREEMENTS_FILE)) {
    fs.writeFileSync(AGREEMENTS_FILE, JSON.stringify([], null, 2), 'utf8');
  }
}

export async function GET() {
  try {
    ensureAgreementsFile();
    const data = fs.readFileSync(AGREEMENTS_FILE, 'utf8');
    const agreements = JSON.parse(data);
    return NextResponse.json(agreements);
  } catch (error) {
    console.error('Error reading agreements.json:', error);
    return NextResponse.json({ error: 'Failed to load agreements' }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    ensureAgreementsFile();
    const record = await request.json();
    
    // Read existing records
    const data = fs.readFileSync(AGREEMENTS_FILE, 'utf8');
    const existingRecords = JSON.parse(data);
    
    // Remove any existing record with the same evalId, testId, and assertionIndex
    const updatedRecords = existingRecords.filter((r: any) =>
      !(r.testId === record.testId && 
        r.assertionIndex === record.assertionIndex && 
        r.evalId === record.evalId)
    );
    
    // Add the new record
    updatedRecords.push(record);
    
    // Write back to file
    fs.writeFileSync(AGREEMENTS_FILE, JSON.stringify(updatedRecords, null, 2), 'utf8');
    
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error saving agreement:', error);
    return NextResponse.json({ error: 'Failed to save agreement' }, { status: 500 });
  }
}

