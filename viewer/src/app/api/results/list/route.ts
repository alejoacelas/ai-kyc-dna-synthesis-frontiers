import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// Data directory: data/raw_results (relative to viewer/)
const RESULTS_DIR = path.join(process.cwd(), '..', 'data', 'raw_results');

export async function GET() {
  try {
    const files = fs.readdirSync(RESULTS_DIR);

    // Filter for JSON files
    const resultsFiles = files
      .filter(file => file.endsWith('.json'))
      .map(file => {
        const filePath = path.join(RESULTS_DIR, file);
        const stats = fs.statSync(filePath);
        return {
          filename: file,
          mtime: stats.mtime.toISOString(),
          mtimeMs: stats.mtime.getTime()
        };
      })
      .sort((a, b) => b.mtimeMs - a.mtimeMs); // Sort by modification time, most recent first

    return NextResponse.json(resultsFiles);
  } catch (error) {
    console.error('Error listing results files:', error);
    return NextResponse.json({ error: 'Failed to list results files' }, { status: 500 });
  }
}

