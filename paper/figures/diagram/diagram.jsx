import React from 'react';

const MethodologyDiagram = () => {
  const colors = {
    blue: '#3B82F6',
    orange: '#F97316',
    green: '#22C55E',
    purple: '#A855F7',
    gray: '#6B7280',
    lightGray: '#E5E7EB',
    darkGray: '#374151',
    white: '#FFFFFF',
    bgLight: '#F9FAFB',
  };

  return (
    <svg viewBox="0 0 900 1050" className="w-full h-auto bg-white">
      <style>
        {`
          .title { font: bold 14px system-ui, sans-serif; fill: #1F2937; }
          .subtitle { font: 11px system-ui, sans-serif; fill: #6B7280; }
          .label { font: 600 11px system-ui, sans-serif; fill: #374151; }
          .small { font: 10px system-ui, sans-serif; fill: #6B7280; }
          .tiny { font: 9px system-ui, sans-serif; fill: #9CA3AF; }
          .metric-title { font: bold 12px system-ui, sans-serif; fill: #1F2937; }
          .table-header { font: 600 9px system-ui, sans-serif; fill: #374151; }
          .table-cell { font: 9px system-ui, sans-serif; fill: #4B5563; }
        `}
      </style>

      {/* Title */}
      <text x="450" y="30" textAnchor="middle" className="title" fontSize="16">
        Evaluation Methodology: Single Customer Trace
      </text>

      {/* ========== CUSTOMER PROFILE CARD ========== */}
      <g transform="translate(325, 50)">
        <rect x="0" y="0" width="250" height="90" rx="6" fill={colors.white} stroke={colors.darkGray} strokeWidth="1.5" />
        <rect x="0" y="0" width="250" height="24" rx="6" fill={colors.darkGray} />
        <rect x="0" y="18" width="250" height="10" fill={colors.darkGray} />
        <text x="125" y="16" textAnchor="middle" fill={colors.white} fontSize="11" fontWeight="600">
          CUSTOMER PROFILE
        </text>
        
        {/* Avatar icon - left aligned */}
        <rect x="12" y="32" width="40" height="50" rx="4" fill={colors.lightGray} stroke={colors.gray} strokeWidth="1" />
        <circle cx="32" cy="47" r="10" fill={colors.gray} />
        <ellipse cx="32" cy="72" rx="14" ry="8" fill={colors.gray} />
        
        {/* Customer details - shifted right to accommodate avatar */}
        <text x="62" y="42" className="label">Dr. Maria Santos</text>
        <text x="62" y="56" className="small">Pacific Biomedical Institute</text>
        <text x="62" y="70" className="small">m.santos@pacificbio.edu</text>
        <text x="62" y="84" className="table-cell" fontStyle="italic">Order: Ebola Virus GP RBD</text>
        
        {/* Reference work annotation */}
        <text x="125" y="105" textAnchor="middle" className="tiny">
          Reference work: Santos et al. (2023) — Ebola vaccine construct
        </text>
      </g>

      {/* Arrow from customer to screeners */}
      <line x1="450" y1="160" x2="450" y2="185" stroke={colors.gray} strokeWidth="2" markerEnd="url(#arrowhead-gray)" />

      {/* ========== SCREENERS SECTION ========== */}
      <g transform="translate(200, 190)">
        {/* AI Models */}
        <g transform="translate(0, 0)">
          <rect x="0" y="0" width="180" height="70" rx="6" fill={colors.bgLight} stroke={colors.gray} strokeWidth="1" />
          <text x="90" y="20" textAnchor="middle" className="label"><tspan fontSize="9" className="emoji">🤖</tspan> AI Models</text>
          <text x="90" y="35" textAnchor="middle" className="tiny">5 models × 2 tool configurations</text>
          {/* Tool icons - logos */}
          <image x="30" y="44" width="16" height="16" href="web-search-logo.png" />
          <image x="58" y="44" width="16" height="16" href="ita-logo.svg" />
          <image x="86" y="44" width="16" height="16" href="europe-pmc-log.png" />
          <image x="114" y="44" width="16" height="16" href="orcid-logo.png" />
        </g>

        {/* Human Baseline */}
        <g transform="translate(320, 0)">
          <rect x="0" y="0" width="180" height="70" rx="6" fill={colors.bgLight} stroke={colors.gray} strokeWidth="1" />
          <text x="90" y="20" textAnchor="middle" className="label"><tspan fontSize="9" className="emoji">👤</tspan> Human Baseline</text>
          <text x="90" y="35" textAnchor="middle" className="tiny">2 expert screeners</text>
          <text x="90" y="55" textAnchor="middle" className="small"><tspan fontSize="9" className="emoji">⏱️</tspan> ~30 min</text>
        </g>

        {/* Convergence lines */}
        <line x1="90" y1="70" x2="90" y2="85" stroke={colors.gray} strokeWidth="1.5" />
        <line x1="410" y1="70" x2="410" y2="85" stroke={colors.gray} strokeWidth="1.5" />
        <line x1="90" y1="85" x2="410" y2="85" stroke={colors.gray} strokeWidth="1.5" />
        <line x1="250" y1="85" x2="250" y2="100" stroke={colors.gray} strokeWidth="1.5" />
      </g>

      {/* ========== EVIDENCE TABLE ========== */}
      <g transform="translate(150, 300)">
        <text x="300" y="0" textAnchor="middle" className="label">EVIDENCE TABLE (Tasks 1-4)</text>
        
        <rect x="0" y="10" width="600" height="120" rx="4" fill={colors.white} stroke={colors.gray} strokeWidth="1" />
        
        {/* Header row */}
        <rect x="0" y="10" width="600" height="22" rx="4" fill={colors.lightGray} />
        <rect x="0" y="28" width="600" height="4" fill={colors.lightGray} />
        <text x="70" y="25" textAnchor="middle" className="table-header">Criterion</text>
        <line x1="140" y1="10" x2="140" y2="130" stroke={colors.lightGray} strokeWidth="1" />
        
        {/* Blue highlighted column header and full column */}
        <rect x="140" y="10" width="160" height="120" fill={colors.blue} fillOpacity="0.08" />
        <rect x="140" y="10" width="160" height="22" fill={colors.blue} fillOpacity="0.15" />
        <text x="220" y="25" textAnchor="middle" className="table-header" fill={colors.blue}>Sources</text>
        <line x1="300" y1="10" x2="300" y2="130" stroke={colors.lightGray} strokeWidth="1" />
        
        {/* Orange highlighted column header and full column */}
        <rect x="300" y="10" width="300" height="120" fill={colors.orange} fillOpacity="0.08" />
        <rect x="300" y="10" width="300" height="22" fill={colors.orange} fillOpacity="0.15" />
        <text x="450" y="25" textAnchor="middle" className="table-header" fill={colors.orange}>Evidence Summary</text>

        {/* Row 1: Affiliation */}
        <line x1="0" y1="55" x2="600" y2="55" stroke={colors.lightGray} strokeWidth="1" />
        <text x="70" y="45" textAnchor="middle" className="table-cell">1. Affiliation</text>
        <text x="220" y="45" textAnchor="middle" className="table-cell" fill={colors.blue}>[epmc1], [web2]</text>
        <text x="450" y="45" textAnchor="middle" className="table-cell" fill={colors.orange}>2023 publication lists author at Pacific Biomed...</text>

        {/* Row 2: Institution */}
        <line x1="0" y1="80" x2="600" y2="80" stroke={colors.lightGray} strokeWidth="1" />
        <text x="70" y="70" textAnchor="middle" className="table-cell">2. Institution</text>
        <text x="220" y="70" textAnchor="middle" className="table-cell" fill={colors.blue}>[web3]</text>
        <text x="450" y="70" textAnchor="middle" className="table-cell" fill={colors.orange}>US-based biomedical research institute...</text>

        {/* Row 3: Email */}
        <line x1="0" y1="105" x2="600" y2="105" stroke={colors.lightGray} strokeWidth="1" />
        <text x="70" y="95" textAnchor="middle" className="table-cell">3. Email</text>
        <text x="220" y="95" textAnchor="middle" className="table-cell" fill={colors.blue}>[web4]</text>
        <text x="450" y="95" textAnchor="middle" className="table-cell" fill={colors.orange}>Domain pacificbio.edu registered to institution...</text>

        {/* Row 4: Sanctions */}
        <text x="70" y="120" textAnchor="middle" className="table-cell">4. Sanctions</text>
        <text x="220" y="120" textAnchor="middle" className="table-cell" fill={colors.blue}>[screen1]</text>
        <text x="450" y="120" textAnchor="middle" className="table-cell" fill={colors.orange}>No matches found in CSL database...</text>

        {/* Column indicators for arrows */}
        <circle cx="220" cy="140" r="4" fill={colors.blue} />
        <circle cx="450" cy="140" r="4" fill={colors.orange} />
      </g>

      {/* ========== DETERMINATION TABLE (Green/Flag Accuracy colored) - Moved lower ========== */}
      <g transform="translate(150, 480)">
        <text x="120" y="0" textAnchor="middle" className="label">DETERMINATION TABLE</text>
        
        {/* Stacked card effect with green tint */}
        <rect x="10" y="18" width="220" height="65" rx="4" fill={colors.green} fillOpacity="0.1" stroke={colors.green} strokeWidth="1" />
        <rect x="5" y="13" width="220" height="65" rx="4" fill={colors.green} fillOpacity="0.05" stroke={colors.green} strokeWidth="1" />
        <rect x="0" y="8" width="220" height="65" rx="4" fill={colors.white} stroke={colors.green} strokeWidth="1.5" />
        
        {/* Header */}
        <rect x="0" y="8" width="220" height="18" rx="4" fill={colors.green} fillOpacity="0.15" />
        <rect x="0" y="22" width="220" height="4" fill={colors.green} fillOpacity="0.15" />
        <text x="70" y="21" textAnchor="middle" className="table-header">Criterion</text>
        <text x="170" y="21" textAnchor="middle" className="table-header">Flag Status</text>
        
        {/* Content row */}
        <text x="70" y="42" textAnchor="middle" className="table-cell">1. Affiliation</text>
        <circle cx="145" cy="39" r="6" fill={colors.green} />
        <text x="165" y="42" className="table-cell">NO FLAG</text>
        
        {/* Dots indicating more */}
        <text x="110" y="62" textAnchor="middle" className="small" fill={colors.gray}>● ● ●  (×3 more)</text>

        {/* Green dot for arrow */}
        <circle cx="110" cy="85" r="4" fill={colors.green} />
      </g>

      {/* ========== BACKGROUND WORK TABLE (Purple/Work Relevance colored) - Moved lower ========== */}
      <g transform="translate(430, 480)">
        <text x="160" y="0" textAnchor="middle" className="label">BACKGROUND WORK TABLE (Task 5)</text>
        
        <rect x="0" y="8" width="320" height="85" rx="4" fill={colors.white} stroke={colors.purple} strokeWidth="1.5" />
        
        {/* Header with purple tint */}
        <rect x="0" y="8" width="320" height="18" rx="4" fill={colors.purple} fillOpacity="0.15" />
        <rect x="0" y="22" width="320" height="4" fill={colors.purple} fillOpacity="0.15" />
        <text x="25" y="21" textAnchor="middle" className="table-header">Rel.</text>
        <text x="90" y="21" textAnchor="middle" className="table-header">Organism</text>
        <text x="165" y="21" textAnchor="middle" className="table-header">Sources</text>
        <text x="255" y="21" textAnchor="middle" className="table-header">Summary</text>

        {/* Expanded row */}
        <line x1="0" y1="50" x2="320" y2="50" stroke={colors.purple} strokeOpacity="0.3" strokeWidth="1" />
        <text x="25" y="42" textAnchor="middle" className="table-cell" fontWeight="600">5</text>
        <text x="90" y="42" textAnchor="middle" className="table-cell">Ebola virus</text>
        <text x="165" y="42" textAnchor="middle" className="table-cell">[epmc4]</text>
        <text x="255" y="42" textAnchor="middle" className="table-cell">GP expression study</text>

        {/* Collapsed rows */}
        <line x1="0" y1="70" x2="320" y2="70" stroke={colors.purple} strokeOpacity="0.3" strokeWidth="1" />
        <text x="25" y="62" textAnchor="middle" className="table-cell">4</text>
        <rect x="60" y="56" width="50" height="7" rx="2" fill={colors.purple} fillOpacity="0.2" />
        <rect x="140" y="56" width="35" height="7" rx="2" fill={colors.purple} fillOpacity="0.2" />
        <rect x="200" y="56" width="70" height="7" rx="2" fill={colors.purple} fillOpacity="0.2" />

        <text x="160" y="82" textAnchor="middle" className="tiny">... (up to 5 works)</text>

        {/* Purple dot for arrow */}
        <circle cx="160" cy="103" r="4" fill={colors.purple} />
      </g>

      {/* ========== METRIC BOXES (Reordered: Flag Accuracy first) ========== */}
      {/* Flag Accuracy - Now leftmost */}
      <g transform="translate(80, 650)">
        <rect x="0" y="0" width="160" height="90" rx="6" fill={colors.white} stroke={colors.green} strokeWidth="2" />
        <rect x="0" y="0" width="160" height="24" rx="6" fill={colors.green} fillOpacity="0.1" />
        <rect x="0" y="20" width="160" height="8" fill={colors.green} fillOpacity="0.1" />
        <text x="80" y="17" textAnchor="middle" className="metric-title" fill={colors.green}>FLAG ACCURACY</text>
        <text x="80" y="40" textAnchor="middle" className="small"><tspan fontSize="9" className="emoji">👤</tspan> Manual grading</text>
        <text x="80" y="55" textAnchor="middle" className="tiny">"Does flag match</text>
        <text x="80" y="67" textAnchor="middle" className="tiny">ground truth?"</text>
        <text x="80" y="82" textAnchor="middle" className="tiny" fill={colors.gray}>×4 criteria</text>
      </g>

      {/* Source Quality */}
      <g transform="translate(270, 650)">
        <rect x="0" y="0" width="160" height="90" rx="6" fill={colors.white} stroke={colors.blue} strokeWidth="2" />
        <rect x="0" y="0" width="160" height="24" rx="6" fill={colors.blue} fillOpacity="0.1" />
        <rect x="0" y="20" width="160" height="8" fill={colors.blue} fillOpacity="0.1" />
        <text x="80" y="17" textAnchor="middle" className="metric-title" fill={colors.blue}>SOURCE QUALITY</text>
        <text x="80" y="40" textAnchor="middle" className="small"><tspan fontSize="9" className="emoji">🤖</tspan> LLM-as-judge</text>
        <text x="80" y="55" textAnchor="middle" className="tiny">"Are sources independently</text>
        <text x="80" y="67" textAnchor="middle" className="tiny">verifiable?"</text>
        <text x="80" y="82" textAnchor="middle" className="tiny" fill={colors.gray}>×4 criteria</text>
      </g>

      {/* Source Fidelity */}
      <g transform="translate(460, 650)">
        <rect x="0" y="0" width="160" height="90" rx="6" fill={colors.white} stroke={colors.orange} strokeWidth="2" />
        <rect x="0" y="0" width="160" height="24" rx="6" fill={colors.orange} fillOpacity="0.1" />
        <rect x="0" y="20" width="160" height="8" fill={colors.orange} fillOpacity="0.1" />
        <text x="80" y="17" textAnchor="middle" className="metric-title" fill={colors.orange}>SOURCE FIDELITY</text>
        <text x="80" y="40" textAnchor="middle" className="small"><tspan fontSize="9" className="emoji">🤖</tspan> LLM-as-judge</text>
        <text x="80" y="55" textAnchor="middle" className="tiny">"Do sources support</text>
        <text x="80" y="67" textAnchor="middle" className="tiny">the claims made?"</text>
        <text x="80" y="82" textAnchor="middle" className="tiny" fill={colors.gray}>×4 criteria</text>
      </g>

      {/* Work Relevance */}
      <g transform="translate(650, 650)">
        <rect x="0" y="0" width="160" height="90" rx="6" fill={colors.white} stroke={colors.purple} strokeWidth="2" />
        <rect x="0" y="0" width="160" height="24" rx="6" fill={colors.purple} fillOpacity="0.1" />
        <rect x="0" y="20" width="160" height="8" fill={colors.purple} fillOpacity="0.1" />
        <text x="80" y="17" textAnchor="middle" className="metric-title" fill={colors.purple}>WORK RELEVANCE</text>
        <text x="80" y="40" textAnchor="middle" className="small"><tspan fontSize="9" className="emoji">🤖</tspan> LLM-as-judge</text>
        <text x="80" y="55" textAnchor="middle" className="tiny">"Is retrieved work as</text>
        <text x="80" y="67" textAnchor="middle" className="tiny">relevant as reference work?"</text>
        <text x="80" y="82" textAnchor="middle" className="tiny" fill={colors.gray}></text>
      </g>

      {/* ========== CONNECTING ARROWS ========== */}
      {/* Green: Determination → Flag Accuracy (leftmost) */}
      <path
        d="M 260 565 L 260 600 Q 260 620 200 630 L 160 640"
        stroke={colors.green}
        strokeWidth="2"
        fill="none"
        markerEnd="url(#arrowhead-22C55E)"
      />

      {/* Blue: Sources column → Source Quality (horizontal first, then down through gap) */}
      <path
        d="M 370 440 L 370 455 L 400 455 L 400 600 Q 400 620 370 630 L 350 640"
        stroke={colors.blue}
        strokeWidth="2"
        fill="none"
        markerEnd="url(#arrowhead-3B82F6)"
      />
      
      {/* Orange: Evidence column → Source Fidelity (horizontal first, then down through gap) */}
      <path
        d="M 600 440 L 600 455 L 415 455 L 415 600 Q 415 620 480 630 L 540 640"
        stroke={colors.orange}
        strokeWidth="2"
        fill="none"
        markerEnd="url(#arrowhead-F97316)"
      />

      {/* Purple: Background Work → Work Relevance */}
      <path
        d="M 590 583 L 590 600 Q 590 620 660 630 L 730 640"
        stroke={colors.purple}
        strokeWidth="2"
        fill="none"
        markerEnd="url(#arrowhead-A855F7)"
      />

      {/* Arrow markers */}
      <defs>
        <marker id="arrowhead-gray" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
          <polygon points="0 0, 10 3.5, 0 7" fill={colors.gray} />
        </marker>
        <marker id="arrowhead-3B82F6" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
          <polygon points="0 0, 10 3.5, 0 7" fill={colors.blue} />
        </marker>
        <marker id="arrowhead-F97316" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
          <polygon points="0 0, 10 3.5, 0 7" fill={colors.orange} />
        </marker>
        <marker id="arrowhead-22C55E" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
          <polygon points="0 0, 10 3.5, 0 7" fill={colors.green} />
        </marker>
        <marker id="arrowhead-A855F7" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
          <polygon points="0 0, 10 3.5, 0 7" fill={colors.purple} />
        </marker>
      </defs>

      {/* ========== AGGREGATION NOTE ========== */}
      <g transform="translate(200, 770)">
        <rect x="0" y="0" width="500" height="50" rx="6" fill={colors.bgLight} stroke={colors.lightGray} strokeWidth="1" strokeDasharray="4,2" />
        <text x="250" y="20" textAnchor="middle" className="small">
          Per customer: 15 binary measurements (5 tasks × 3 metrics)
        </text>
        <text x="250" y="38" textAnchor="middle" className="tiny">
          Aggregated across 41 customers × (10 AI configurations + human baseline)
        </text>
      </g>
    </svg>
  );
};

export default MethodologyDiagram;