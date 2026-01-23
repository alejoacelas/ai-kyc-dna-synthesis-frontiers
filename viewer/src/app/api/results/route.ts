import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// Data directory: data/raw_results (relative to viewer/)
const DATA_DIR = path.join(process.cwd(), '..', 'data');
const RESULTS_DIR = path.join(DATA_DIR, 'raw_results');

function getAllResultsFiles() {
  const files = fs.readdirSync(RESULTS_DIR);

  // Filter for results JSON files
  const resultsFiles = files
    .filter(file => file.endsWith('.json'))
    .map(file => ({
      name: file,
      path: path.join(RESULTS_DIR, file),
      mtime: fs.statSync(path.join(RESULTS_DIR, file)).mtime.getTime()
    }))
    .sort((a, b) => b.mtime - a.mtime); // Sort by modification time, most recent first

  return resultsFiles;
}

function getMostRecentResultsFile(): string {
  const resultsFiles = getAllResultsFiles();
  
  if (resultsFiles.length === 0) {
    throw new Error('No results files found');
  }
  
  return resultsFiles[0].path;
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const filename = searchParams.get('file');
    
    let resultsPath: string;
    
    if (filename) {
      // Sanitize filename to prevent path traversal
      const sanitizedFilename = path.basename(filename);
      if (sanitizedFilename !== filename || !sanitizedFilename.endsWith('.json')) {
        return NextResponse.json({ error: 'Invalid filename' }, { status: 400 });
      }
      // Load specific file from results directory
      resultsPath = path.join(RESULTS_DIR, sanitizedFilename);
      if (!fs.existsSync(resultsPath)) {
        return NextResponse.json({ error: 'File not found' }, { status: 404 });
      }
    } else {
      // Load most recent file
      resultsPath = getMostRecentResultsFile();
    }
    
    const data = fs.readFileSync(resultsPath, 'utf8');
    const results = JSON.parse(data);

    return NextResponse.json(results);
  } catch (error) {
    console.error('Error reading results file:', error);
    return NextResponse.json({ error: 'Failed to load results' }, { status: 500 });
  }
}