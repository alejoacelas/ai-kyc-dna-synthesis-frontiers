import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const DATA_DIR = path.join(process.cwd(), '..', 'data');
const BLIND_GRADINGS_FILE = path.join(DATA_DIR, 'blind_gradings.json');

function ensureBlindGradingsFile() {
  if (!fs.existsSync(BLIND_GRADINGS_FILE)) {
    fs.writeFileSync(BLIND_GRADINGS_FILE, JSON.stringify([], null, 2), 'utf8');
  }
}

export async function GET() {
  try {
    ensureBlindGradingsFile();
    const data = fs.readFileSync(BLIND_GRADINGS_FILE, 'utf8');
    const gradings = JSON.parse(data);
    return NextResponse.json(gradings);
  } catch (error) {
    console.error('Error reading blind_gradings.json:', error);
    return NextResponse.json({ error: 'Failed to load blind gradings' }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    ensureBlindGradingsFile();
    const record = await request.json();

    // Read existing records
    const data = fs.readFileSync(BLIND_GRADINGS_FILE, 'utf8');
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
    fs.writeFileSync(BLIND_GRADINGS_FILE, JSON.stringify(updatedRecords, null, 2), 'utf8');

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error saving blind grading:', error);
    return NextResponse.json({ error: 'Failed to save blind grading' }, { status: 500 });
  }
}
