const pptxgen = require('pptxgenjs');
const fs = require('fs');
const path = require('path');

// Color palette - Enterprise AI theme (no # prefix for pptxgenjs)
const colors = {
  darkNavy: '1C2833',
  charcoal: '2E4053',
  teal: '5EA8A7',
  gold: 'BF9A4A',
  white: 'FFFFFF',
  lightGray: 'F4F6F6',
  mediumGray: 'AAB7B8',
  darkText: '1C2833',
  success: '27AE60',
  accent: '3498DB',
  red: 'E74C3C',
  purple: '9B59B6'
};

async function createPresentation() {
  console.log('Creating AI Force Assess presentation...\n');

  const pptx = new pptxgen();
  pptx.layout = 'LAYOUT_16x9';
  pptx.author = 'AI Force Assess Team';
  pptx.title = 'AI Force Assess - Building Enterprise AI with Agentic Development';
  pptx.subject = 'Executive Briefing';

  // ========== SLIDE 1: Title ==========
  let slide = pptx.addSlide();
  slide.background = { color: colors.darkNavy };

  // Logo bar
  slide.addText('AI FORCE ASSESS', { x: 0.4, y: 0.3, w: 3, h: 0.4, fontSize: 12, bold: true, color: colors.gold, fontFace: 'Arial' });

  // Main title
  slide.addText('Building Enterprise AI with Agentic Development', {
    x: 0.5, y: 1.5, w: 9, h: 1, fontSize: 36, bold: true, color: colors.white, fontFace: 'Arial', align: 'center'
  });

  // Accent line
  slide.addShape(pptx.shapes.RECTANGLE, { x: 4, y: 2.6, w: 2, h: 0.05, fill: { color: colors.teal } });

  // Subtitle
  slide.addText('Transforming CMDB Data into Cloud Migration Intelligence', {
    x: 0.5, y: 2.8, w: 9, h: 0.5, fontSize: 18, color: colors.teal, fontFace: 'Arial', align: 'center'
  });

  // Tagline
  slide.addText('Executive Briefing | December 2025', {
    x: 0.5, y: 3.4, w: 9, h: 0.4, fontSize: 12, color: colors.mediumGray, fontFace: 'Arial', align: 'center'
  });

  // Footer
  slide.addText('Confidential - Internal Use Only', {
    x: 0.5, y: 5, w: 9, h: 0.3, fontSize: 10, color: colors.mediumGray, fontFace: 'Arial', align: 'center'
  });

  // ========== SLIDE 2: The Challenge ==========
  slide = pptx.addSlide();
  slide.background = { color: colors.lightGray };

  // Header
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.8, fill: { color: colors.darkNavy } });
  slide.addText('The Challenge', { x: 0.4, y: 0.2, w: 5, h: 0.5, fontSize: 22, bold: true, color: colors.white, fontFace: 'Arial' });

  // Left column - Pain points
  slide.addText('Current State Pain Points', { x: 0.4, y: 1.1, w: 4.5, h: 0.4, fontSize: 14, bold: true, color: colors.darkNavy, fontFace: 'Arial' });

  const painPoints = [
    'Cloud migration assessments are manual, time-consuming, and expert-dependent',
    'Inconsistent 6R recommendations across different consultants and engagements',
    'Limited visibility into decommission candidates buried in CMDB data',
    'Scaling expertise is expensive - senior architects are a scarce resource'
  ];

  painPoints.forEach((point, i) => {
    slide.addShape(pptx.shapes.RECTANGLE, { x: 0.4, y: 1.6 + i * 0.75, w: 4.5, h: 0.65, fill: { color: colors.white }, line: { color: colors.red, pt: 0, dashType: 'solid' } });
    slide.addShape(pptx.shapes.RECTANGLE, { x: 0.4, y: 1.6 + i * 0.75, w: 0.06, h: 0.65, fill: { color: colors.red } });
    slide.addText(point, { x: 0.55, y: 1.65 + i * 0.75, w: 4.2, h: 0.55, fontSize: 10, color: colors.darkText, fontFace: 'Arial', valign: 'middle' });
  });

  // Right column - Stats
  slide.addText('Traditional Approach Cost', { x: 5.3, y: 1.1, w: 4.3, h: 0.4, fontSize: 14, bold: true, color: colors.darkNavy, fontFace: 'Arial' });

  const stats = [
    { num: '15', label: 'Person Development Team' },
    { num: '8 Months', label: 'Development Timeline' },
    { num: '$500K+', label: 'Estimated Investment' }
  ];

  stats.forEach((stat, i) => {
    slide.addShape(pptx.shapes.RECTANGLE, { x: 5.3, y: 1.55 + i * 0.85, w: 4.3, h: 0.75, fill: { color: colors.darkNavy }, rectRadius: 0.05 });
    slide.addText(stat.num, { x: 5.3, y: 1.55 + i * 0.85, w: 4.3, h: 0.45, fontSize: 24, bold: true, color: colors.gold, fontFace: 'Arial', align: 'center' });
    slide.addText(stat.label, { x: 5.3, y: 1.95 + i * 0.85, w: 4.3, h: 0.3, fontSize: 10, color: colors.white, fontFace: 'Arial', align: 'center' });
  });

  // Opportunity box
  slide.addShape(pptx.shapes.RECTANGLE, { x: 5.3, y: 4.2, w: 4.3, h: 0.6, fill: { color: colors.teal }, rectRadius: 0.05 });
  slide.addText('Opportunity: Leverage AI to accelerate and democratize this capability', {
    x: 5.3, y: 4.2, w: 4.3, h: 0.6, fontSize: 10, color: colors.white, fontFace: 'Arial', align: 'center', valign: 'middle'
  });

  // ========== SLIDE 3: The Solution ==========
  slide = pptx.addSlide();
  slide.background = { color: colors.lightGray };

  // Header
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.8, fill: { color: colors.darkNavy } });
  slide.addText('The Solution: AI Force Assess', { x: 0.4, y: 0.2, w: 6, h: 0.5, fontSize: 22, bold: true, color: colors.white, fontFace: 'Arial' });

  // Center title
  slide.addText('End-to-End CMDB Assessment Platform', { x: 0.5, y: 1, w: 9, h: 0.4, fontSize: 16, bold: true, color: colors.darkNavy, fontFace: 'Arial', align: 'center' });
  slide.addText('Intelligent migration recommendations powered by 17 CrewAI agents', { x: 0.5, y: 1.35, w: 9, h: 0.3, fontSize: 11, color: colors.charcoal, fontFace: 'Arial', align: 'center' });

  // Feature cards - 2 rows of 3
  const features = [
    { title: 'Discovery Flow', desc: 'Automated CMDB data ingestion and intelligent asset categorization' },
    { title: 'Collection Flow', desc: 'Adaptive questionnaires that fill data gaps based on analysis' },
    { title: 'Assessment Flow', desc: '6R migration recommendations with confidence scores' },
    { title: 'Plan Flow', desc: 'Wave planning and migration sequencing' },
    { title: 'Decommission', desc: 'Identify retirement candidates with cost savings' },
    { title: 'API-First', desc: 'Full REST API for enterprise integration and MCP' }
  ];

  features.forEach((feat, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.5 + col * 3.1;
    const y = 1.8 + row * 1.3;

    slide.addShape(pptx.shapes.RECTANGLE, { x, y, w: 2.9, h: 1.15, fill: { color: colors.white }, rectRadius: 0.05, shadow: { type: 'outer', blur: 3, offset: 1, angle: 45, opacity: 0.15 } });
    slide.addShape(pptx.shapes.RECTANGLE, { x, y, w: 2.9, h: 0.05, fill: { color: colors.teal } });
    slide.addText(feat.title, { x, y: y + 0.15, w: 2.9, h: 0.35, fontSize: 11, bold: true, color: colors.darkNavy, fontFace: 'Arial', align: 'center' });
    slide.addText(feat.desc, { x: x + 0.1, y: y + 0.5, w: 2.7, h: 0.55, fontSize: 9, color: colors.charcoal, fontFace: 'Arial', align: 'center', valign: 'top' });
  });

  // Bottom bar
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0, y: 4.55, w: 10, h: 0.7, fill: { color: colors.charcoal } });
  const bottomItems = [
    { highlight: 'Multi-Tenant', sub: 'Enterprise data isolation' },
    { highlight: 'Real-Time', sub: 'Agent observability' },
    { highlight: 'Extensible', sub: 'Portfolio analysis ready' }
  ];
  bottomItems.forEach((item, i) => {
    slide.addText(item.highlight, { x: 1.5 + i * 2.8, y: 4.6, w: 2.5, h: 0.3, fontSize: 11, bold: true, color: colors.gold, fontFace: 'Arial', align: 'center' });
    slide.addText(item.sub, { x: 1.5 + i * 2.8, y: 4.85, w: 2.5, h: 0.25, fontSize: 9, color: colors.white, fontFace: 'Arial', align: 'center' });
  });

  // ========== SLIDE 4: The Innovation ==========
  slide = pptx.addSlide();
  slide.background = { color: colors.darkNavy };

  // Header
  slide.addText('The Innovation: Agentic Development', { x: 0.4, y: 0.3, w: 7, h: 0.5, fontSize: 22, bold: true, color: colors.white, fontFace: 'Arial' });
  slide.addText('AI-Assisted Software Engineering at Scale', { x: 0.4, y: 0.75, w: 5, h: 0.3, fontSize: 12, color: colors.teal, fontFace: 'Arial' });

  // Tool cards - 2x2 grid
  const tools = [
    { title: 'Cursor IDE', desc: 'AI-powered code completion, refactoring, and intelligent suggestions' },
    { title: 'Claude Code (CC)', desc: 'Autonomous coding agent for complex multi-file changes' },
    { title: 'CrewAI Framework', desc: '17 specialized AI agents working collaboratively on analysis' },
    { title: 'GitHub Projects', desc: 'Agile delivery with 10 iterations, 20 milestones' }
  ];

  tools.forEach((tool, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.4 + col * 2.95;
    const y = 1.2 + row * 0.9;

    slide.addShape(pptx.shapes.RECTANGLE, { x, y, w: 2.85, h: 0.8, fill: { color: '3D5066' }, rectRadius: 0.05, line: { color: '5A6E80', pt: 0.5 } });
    slide.addText(tool.title, { x, y: y + 0.05, w: 2.85, h: 0.3, fontSize: 11, bold: true, color: colors.gold, fontFace: 'Arial', align: 'center' });
    slide.addText(tool.desc, { x: x + 0.1, y: y + 0.35, w: 2.65, h: 0.4, fontSize: 8, color: colors.white, fontFace: 'Arial', align: 'center' });
  });

  // Agent categories box
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0.4, y: 3.1, w: 5.9, h: 1.5, fill: { color: '2D5A59' }, rectRadius: 0.05, line: { color: colors.teal, pt: 0.5 } });
  slide.addText('AI Agent Categories', { x: 0.5, y: 3.2, w: 5.7, h: 0.3, fontSize: 11, bold: true, color: colors.white, fontFace: 'Arial' });

  const agents = [
    'Discovery Agents (4): Data analysis, CMDB parsing, dependency mapping',
    'Assessment Agents (2): Migration strategy, risk assessment',
    'Planning Agents (1): Wave planning, sequencing coordination',
    'Learning Agents (3): Pattern recognition, context management',
    'Observability Agents (3): Health monitoring, performance tracking'
  ];
  agents.forEach((agent, i) => {
    slide.addText(agent, { x: 0.6, y: 3.5 + i * 0.22, w: 5.5, h: 0.22, fontSize: 8, color: colors.white, fontFace: 'Arial' });
  });

  // Right side stats
  const rightStats = [
    { num: '38', label: 'Architecture Decision Records' },
    { num: '3-5x', label: 'Development velocity increase' },
    { num: '7', label: 'Enterprise architecture layers' },
    { num: '100%', label: 'API coverage for integration' }
  ];

  rightStats.forEach((stat, i) => {
    slide.addShape(pptx.shapes.RECTANGLE, { x: 6.5, y: 1.2 + i * 0.8, w: 3.1, h: 0.7, fill: { color: colors.white }, rectRadius: 0.05 });
    slide.addText(stat.num, { x: 6.5, y: 1.22 + i * 0.8, w: 0.9, h: 0.66, fontSize: 18, bold: true, color: colors.teal, fontFace: 'Arial', align: 'center', valign: 'middle' });
    slide.addText(stat.label, { x: 7.4, y: 1.22 + i * 0.8, w: 2.1, h: 0.66, fontSize: 9, color: colors.darkNavy, fontFace: 'Arial', valign: 'middle' });
  });

  // ========== SLIDE 5: Team Transformation ==========
  slide = pptx.addSlide();
  slide.background = { color: colors.lightGray };

  // Header
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.9, fill: { color: colors.darkNavy } });
  slide.addText('Team Transformation Story', { x: 0.4, y: 0.15, w: 6, h: 0.4, fontSize: 22, bold: true, color: colors.white, fontFace: 'Arial' });
  slide.addText('From Zero AI Experience to Production-Ready in 6 Months', { x: 0.4, y: 0.5, w: 6, h: 0.3, fontSize: 11, color: colors.teal, fontFace: 'Arial' });

  // Left column - Team roles
  slide.addText('Team Composition & Growth', { x: 0.4, y: 1.05, w: 4.5, h: 0.35, fontSize: 13, bold: true, color: colors.darkNavy, fontFace: 'Arial' });

  const roles = [
    { num: '9', desc: 'Freshers -> QA Team (Onboarding)' },
    { num: '2', desc: 'PMs -> Product Team' },
    { num: '2', desc: 'Tech Resources -> QA Testers' },
    { num: '2', desc: 'Architects -> AI Engineers / Developers' },
    { num: '1', desc: 'DevOps Engineer' }
  ];

  roles.forEach((role, i) => {
    slide.addShape(pptx.shapes.RECTANGLE, { x: 0.4, y: 1.45 + i * 0.5, w: 4.6, h: 0.45, fill: { color: colors.white }, rectRadius: 0.03, shadow: { type: 'outer', blur: 2, offset: 1, angle: 45, opacity: 0.1 } });
    slide.addShape(pptx.shapes.OVAL, { x: 0.5, y: 1.5 + i * 0.5, w: 0.35, h: 0.35, fill: { color: colors.teal } });
    slide.addText(role.num, { x: 0.5, y: 1.5 + i * 0.5, w: 0.35, h: 0.35, fontSize: 10, bold: true, color: colors.white, fontFace: 'Arial', align: 'center', valign: 'middle' });
    slide.addText(role.desc, { x: 1, y: 1.45 + i * 0.5, w: 3.9, h: 0.45, fontSize: 10, color: colors.darkNavy, fontFace: 'Arial', valign: 'middle' });
  });

  // Skills box
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0.4, y: 4, w: 4.6, h: 1.2, fill: { color: colors.charcoal }, rectRadius: 0.05 });
  slide.addText('Skills Developed', { x: 0.5, y: 4.08, w: 4.4, h: 0.25, fontSize: 11, bold: true, color: colors.gold, fontFace: 'Arial' });
  const skills = ['Agentic AI Development (Cursor, Claude Code)', 'Agile/Scrum Methodology', 'GitHub Workflows & Project Management', 'Docker Containerization', 'Roadmap Planning & Milestone Execution'];
  skills.forEach((skill, i) => {
    slide.addText(skill, { x: 0.6, y: 4.35 + i * 0.16, w: 4.3, h: 0.16, fontSize: 8, color: colors.white, fontFace: 'Arial' });
  });

  // Right column - Leadership
  slide.addShape(pptx.shapes.RECTANGLE, { x: 5.2, y: 1.05, w: 4.4, h: 1.45, fill: { color: colors.gold }, rectRadius: 0.05 });
  slide.addText('Leadership Consolidation', { x: 5.3, y: 1.15, w: 4.2, h: 0.3, fontSize: 12, bold: true, color: colors.darkNavy, fontFace: 'Arial' });
  const leaderRoles = ['Product Owner', 'Technical Lead', 'AI Architect', 'Lead Developer', 'Lead QA'];
  leaderRoles.forEach((role, i) => {
    slide.addText(role, { x: 5.4, y: 1.5 + i * 0.19, w: 4, h: 0.19, fontSize: 9, color: colors.darkNavy, fontFace: 'Arial' });
  });

  // Timeline box
  slide.addShape(pptx.shapes.RECTANGLE, { x: 5.2, y: 2.65, w: 4.4, h: 1.1, fill: { color: colors.white }, rectRadius: 0.05, line: { color: colors.teal, pt: 0, dashType: 'solid' } });
  slide.addShape(pptx.shapes.RECTANGLE, { x: 5.2, y: 2.65, w: 0.06, h: 1.1, fill: { color: colors.teal } });
  slide.addText('Journey Timeline', { x: 5.35, y: 2.72, w: 4.15, h: 0.25, fontSize: 11, bold: true, color: colors.darkNavy, fontFace: 'Arial' });
  const timeline = ['Month 1-2: Tool setup, basic training, first commits', 'Month 3-4: Independent feature development begins', 'Month 5-6: Full team velocity, production-ready delivery'];
  timeline.forEach((item, i) => {
    slide.addText(item, { x: 5.4, y: 3 + i * 0.22, w: 4.1, h: 0.22, fontSize: 8, color: colors.charcoal, fontFace: 'Arial' });
  });

  // ========== SLIDE 6: By The Numbers ==========
  slide = pptx.addSlide();
  slide.background = { color: colors.lightGray };

  // Header
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.8, fill: { color: colors.darkNavy } });
  slide.addText('By The Numbers', { x: 0.4, y: 0.2, w: 5, h: 0.5, fontSize: 22, bold: true, color: colors.white, fontFace: 'Arial' });

  // Metrics grid - 4x2
  const metrics = [
    { num: '3,497', label: 'Total Commits' },
    { num: '835', label: 'Issues Created' },
    { num: '705', label: 'Issues Closed' },
    { num: '84%', label: 'Closure Rate' },
    { num: '404', label: 'Bugs Fixed' },
    { num: '273', label: 'PRs Merged' },
    { num: '20', label: 'Milestones' },
    { num: '38', label: 'ADRs' }
  ];

  metrics.forEach((m, i) => {
    const col = i % 4;
    const row = Math.floor(i / 4);
    const x = 0.4 + col * 1.55;
    const y = 1 + row * 1.35;

    slide.addShape(pptx.shapes.RECTANGLE, { x, y, w: 1.45, h: 1.2, fill: { color: colors.white }, rectRadius: 0.06, shadow: { type: 'outer', blur: 3, offset: 1, angle: 45, opacity: 0.12 } });
    slide.addShape(pptx.shapes.RECTANGLE, { x, y: y + 1.1, w: 1.45, h: 0.1, fill: { color: colors.teal } });
    slide.addText(m.num, { x, y: y + 0.15, w: 1.45, h: 0.55, fontSize: 22, bold: true, color: colors.teal, fontFace: 'Arial', align: 'center' });
    slide.addText(m.label, { x, y: y + 0.7, w: 1.45, h: 0.35, fontSize: 9, color: colors.darkNavy, fontFace: 'Arial', align: 'center' });
  });

  // Chart area
  slide.addShape(pptx.shapes.RECTANGLE, { x: 6.6, y: 1, w: 3.1, h: 3.5, fill: { color: colors.white }, rectRadius: 0.06, shadow: { type: 'outer', blur: 3, offset: 1, angle: 45, opacity: 0.12 } });
  slide.addText('Monthly Commit Velocity', { x: 6.6, y: 1.1, w: 3.1, h: 0.35, fontSize: 11, bold: true, color: colors.darkNavy, fontFace: 'Arial', align: 'center' });

  // Add the bar chart
  const chartData = [{
    name: 'Commits',
    labels: ['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov'],
    values: [111, 620, 471, 618, 315, 707, 555]
  }];

  slide.addChart(pptx.charts.BAR, chartData, {
    x: 6.7, y: 1.5, w: 2.9, h: 2.9,
    barDir: 'col',
    showTitle: false,
    showLegend: false,
    chartColors: [colors.teal],
    valAxisMaxVal: 800,
    valAxisMinVal: 0,
    catAxisLabelFontSize: 8,
    valAxisLabelFontSize: 8,
    dataLabelPosition: 'outEnd',
    dataLabelFontSize: 7,
    showValue: true
  });

  // ========== SLIDE 7: Cost Efficiency ==========
  slide = pptx.addSlide();
  slide.background = { color: colors.lightGray };

  // Header
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.8, fill: { color: colors.darkNavy } });
  slide.addText('Cost Efficiency Comparison', { x: 0.4, y: 0.2, w: 6, h: 0.5, fontSize: 22, bold: true, color: colors.white, fontFace: 'Arial' });

  // Traditional approach card
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0.5, y: 1, w: 3.6, h: 3.5, fill: { color: colors.white }, rectRadius: 0.08, shadow: { type: 'outer', blur: 4, offset: 2, angle: 45, opacity: 0.15 } });
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0.5, y: 1, w: 3.6, h: 0.55, fill: { color: colors.charcoal }, rectRadius: 0.08 });
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0.5, y: 1.35, w: 3.6, h: 0.2, fill: { color: colors.charcoal } });
  slide.addText('Traditional Approach', { x: 0.5, y: 1.05, w: 3.6, h: 0.45, fontSize: 14, bold: true, color: colors.white, fontFace: 'Arial', align: 'center' });

  const tradStats = [
    { label: 'Team Size', value: '15 Engineers', color: colors.red },
    { label: 'Timeline', value: '8 Months', color: colors.red },
    { label: 'Total Cost', value: '~$500K', color: colors.red },
    { label: 'Documentation', value: 'Variable', color: colors.charcoal }
  ];

  tradStats.forEach((stat, i) => {
    slide.addShape(pptx.shapes.RECTANGLE, { x: 0.6, y: 1.7 + i * 0.7, w: 3.4, h: 0.6, fill: { color: colors.lightGray } });
    slide.addText(stat.label, { x: 0.7, y: 1.7 + i * 0.7, w: 1.5, h: 0.6, fontSize: 10, color: colors.charcoal, fontFace: 'Arial', valign: 'middle' });
    slide.addText(stat.value, { x: 2.2, y: 1.7 + i * 0.7, w: 1.7, h: 0.6, fontSize: 11, bold: true, color: stat.color, fontFace: 'Arial', align: 'right', valign: 'middle' });
  });

  // Agentic approach card
  slide.addShape(pptx.shapes.RECTANGLE, { x: 4.3, y: 1, w: 3.6, h: 3.5, fill: { color: colors.white }, rectRadius: 0.08, shadow: { type: 'outer', blur: 4, offset: 2, angle: 45, opacity: 0.15 } });
  slide.addShape(pptx.shapes.RECTANGLE, { x: 4.3, y: 1, w: 3.6, h: 0.55, fill: { color: colors.teal }, rectRadius: 0.08 });
  slide.addShape(pptx.shapes.RECTANGLE, { x: 4.3, y: 1.35, w: 3.6, h: 0.2, fill: { color: colors.teal } });
  slide.addText('Agentic Approach', { x: 4.3, y: 1.05, w: 3.6, h: 0.45, fontSize: 14, bold: true, color: colors.white, fontFace: 'Arial', align: 'center' });

  const agentStats = [
    { label: 'Team Size', value: '~10 Members', color: colors.success },
    { label: 'Timeline', value: '6.5 Months', color: colors.success },
    { label: 'Total Cost', value: '~$300K', color: colors.success },
    { label: 'Documentation', value: '38 ADRs', color: colors.success }
  ];

  agentStats.forEach((stat, i) => {
    slide.addShape(pptx.shapes.RECTANGLE, { x: 4.4, y: 1.7 + i * 0.7, w: 3.4, h: 0.6, fill: { color: colors.lightGray } });
    slide.addText(stat.label, { x: 4.5, y: 1.7 + i * 0.7, w: 1.5, h: 0.6, fontSize: 10, color: colors.charcoal, fontFace: 'Arial', valign: 'middle' });
    slide.addText(stat.value, { x: 6, y: 1.7 + i * 0.7, w: 1.7, h: 0.6, fontSize: 11, bold: true, color: stat.color, fontFace: 'Arial', align: 'right', valign: 'middle' });
  });

  // Savings box
  slide.addShape(pptx.shapes.RECTANGLE, { x: 8.1, y: 1.5, w: 1.6, h: 2.5, fill: { color: colors.success }, rectRadius: 0.1 });
  slide.addText('40%', { x: 8.1, y: 1.8, w: 1.6, h: 0.8, fontSize: 36, bold: true, color: colors.white, fontFace: 'Arial', align: 'center' });
  slide.addText('Cost Savings', { x: 8.1, y: 2.6, w: 1.6, h: 0.4, fontSize: 11, color: colors.white, fontFace: 'Arial', align: 'center' });
  slide.addText('~$200K saved', { x: 8.1, y: 3, w: 1.6, h: 0.3, fontSize: 9, color: colors.white, fontFace: 'Arial', align: 'center' });

  // ========== SLIDE 8: Architecture Overview ==========
  slide = pptx.addSlide();
  slide.background = { color: colors.lightGray };

  // Header
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.8, fill: { color: colors.darkNavy } });
  slide.addText('Architecture Overview', { x: 0.4, y: 0.2, w: 5, h: 0.5, fontSize: 22, bold: true, color: colors.white, fontFace: 'Arial' });

  // 7 layers
  const layers = [
    { name: '1. API Layer (FastAPI)', desc: 'Request handling, validation, routing', color: colors.darkNavy },
    { name: '2. Service Layer', desc: 'Business logic, orchestration, workflows', color: colors.charcoal },
    { name: '3. Repository Layer', desc: 'Database abstraction, data access', color: colors.teal },
    { name: '4. Model Layer', desc: 'SQLAlchemy + Pydantic structures', color: colors.gold },
    { name: '5. Cache Layer', desc: 'Redis/in-memory optimization', color: colors.success },
    { name: '6. Queue Layer', desc: 'Async processing, background tasks', color: colors.accent },
    { name: '7. Integration Layer', desc: 'External services, AI providers, MCP', color: colors.purple }
  ];

  layers.forEach((layer, i) => {
    slide.addShape(pptx.shapes.RECTANGLE, { x: 0.4, y: 1 + i * 0.55, w: 5.8, h: 0.5, fill: { color: layer.color }, rectRadius: 0.03 });
    slide.addText(layer.name, { x: 0.5, y: 1 + i * 0.55, w: 2.5, h: 0.5, fontSize: 10, bold: true, color: layer.color === colors.gold ? colors.darkNavy : colors.white, fontFace: 'Arial', valign: 'middle' });
    slide.addText(layer.desc, { x: 3, y: 1 + i * 0.55, w: 3.1, h: 0.5, fontSize: 9, color: layer.color === colors.gold ? colors.darkNavy : colors.white, fontFace: 'Arial', align: 'right', valign: 'middle' });
  });

  // Right side boxes
  // Frontend Stack
  slide.addShape(pptx.shapes.RECTANGLE, { x: 6.4, y: 1, w: 3.2, h: 1.1, fill: { color: colors.white }, rectRadius: 0.05, shadow: { type: 'outer', blur: 2, offset: 1, angle: 45, opacity: 0.1 } });
  slide.addText('Frontend Stack', { x: 6.5, y: 1.05, w: 3, h: 0.25, fontSize: 10, bold: true, color: colors.darkNavy, fontFace: 'Arial' });
  slide.addText('Next.js / React\nTanStack Query\nTypeScript\nTailwind CSS', { x: 6.5, y: 1.3, w: 3, h: 0.75, fontSize: 8, color: colors.charcoal, fontFace: 'Arial' });

  // Backend Stack
  slide.addShape(pptx.shapes.RECTANGLE, { x: 6.4, y: 2.2, w: 3.2, h: 1.1, fill: { color: colors.white }, rectRadius: 0.05, shadow: { type: 'outer', blur: 2, offset: 1, angle: 45, opacity: 0.1 } });
  slide.addText('Backend Stack', { x: 6.5, y: 2.25, w: 3, h: 0.25, fontSize: 10, bold: true, color: colors.darkNavy, fontFace: 'Arial' });
  slide.addText('FastAPI (async)\nSQLAlchemy + PostgreSQL\npgvector for embeddings\nCrewAI agents', { x: 6.5, y: 2.5, w: 3, h: 0.75, fontSize: 8, color: colors.charcoal, fontFace: 'Arial' });

  // Codebase Size
  slide.addShape(pptx.shapes.RECTANGLE, { x: 6.4, y: 3.4, w: 3.2, h: 1.1, fill: { color: colors.darkNavy }, rectRadius: 0.05 });
  slide.addText('Codebase Size', { x: 6.5, y: 3.45, w: 3, h: 0.25, fontSize: 10, bold: true, color: colors.gold, fontFace: 'Arial' });
  slide.addText('~485K lines Python (backend)\n~289K lines TypeScript (frontend)\nDocker containerized', { x: 6.5, y: 3.7, w: 3, h: 0.75, fontSize: 8, color: colors.white, fontFace: 'Arial' });

  // ========== SLIDE 9: Live Demo ==========
  slide = pptx.addSlide();
  slide.background = { color: colors.darkNavy };

  // Title
  slide.addText('Live Demo', { x: 0.5, y: 1.2, w: 9, h: 0.7, fontSize: 34, bold: true, color: colors.white, fontFace: 'Arial', align: 'center' });
  slide.addText('End-to-End Assessment Workflow', { x: 0.5, y: 1.85, w: 9, h: 0.4, fontSize: 14, color: colors.teal, fontFace: 'Arial', align: 'center' });

  // Flow steps
  const flowSteps = [
    { num: '1', title: 'Discovery', desc: 'Import CMDB data and analyze assets' },
    { num: '2', title: 'Collection', desc: 'Intelligent questionnaire generation' },
    { num: '3', title: 'Assessment', desc: '6R recommendations with confidence' },
    { num: '4', title: 'Plan', desc: 'Wave planning and sequencing' }
  ];

  flowSteps.forEach((step, i) => {
    const x = 0.7 + i * 2.4;

    slide.addShape(pptx.shapes.RECTANGLE, { x, y: 2.5, w: 2, h: 1.6, fill: { color: '3D5066' }, rectRadius: 0.08, line: { color: '5A6E80', pt: 0.5 } });
    slide.addShape(pptx.shapes.OVAL, { x: x + 0.75, y: 2.6, w: 0.5, h: 0.5, fill: { color: colors.teal } });
    slide.addText(step.num, { x: x + 0.75, y: 2.6, w: 0.5, h: 0.5, fontSize: 14, bold: true, color: colors.white, fontFace: 'Arial', align: 'center', valign: 'middle' });
    slide.addText(step.title, { x, y: 3.2, w: 2, h: 0.35, fontSize: 12, bold: true, color: colors.gold, fontFace: 'Arial', align: 'center' });
    slide.addText(step.desc, { x: x + 0.1, y: 3.55, w: 1.8, h: 0.5, fontSize: 8, color: colors.white, fontFace: 'Arial', align: 'center' });

    // Arrow between steps
    if (i < 3) {
      slide.addText('->', { x: x + 2, y: 3, w: 0.4, h: 0.5, fontSize: 18, color: colors.teal, fontFace: 'Arial', align: 'center', valign: 'middle' });
    }
  });

  // Footer note
  slide.addText('Demo Duration: ~8-10 minutes | Using sanitized sample data', { x: 0.5, y: 4.6, w: 9, h: 0.3, fontSize: 10, color: colors.mediumGray, fontFace: 'Arial', align: 'center' });

  // ========== SLIDE 10: Roadmap ==========
  slide = pptx.addSlide();
  slide.background = { color: colors.lightGray };

  // Header
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.8, fill: { color: colors.darkNavy } });
  slide.addText('Roadmap & Future Vision', { x: 0.4, y: 0.2, w: 6, h: 0.5, fontSize: 22, bold: true, color: colors.white, fontFace: 'Arial' });

  // Three phases
  const phases = [
    {
      title: 'Current Phase',
      period: 'Q4 2025',
      items: ['Complete QA team onboarding', 'Finalize Plan Flow implementation', 'Internal alpha testing', 'Documentation and training materials'],
      status: 'In Progress',
      color: colors.teal
    },
    {
      title: 'Next Phase',
      period: 'Q1 2026',
      items: ['Beta testers on live engagements', 'Decommission flow completion', 'Integration with existing tooling', 'Performance optimization'],
      status: 'Planned',
      color: colors.gold
    },
    {
      title: 'Future Vision',
      period: '2026+',
      items: ['Portfolio analysis extension', 'External client pilots', 'MCP server marketplace', 'Cross-org methodology adoption'],
      status: 'Vision',
      color: colors.accent
    }
  ];

  phases.forEach((phase, i) => {
    const x = 0.4 + i * 3.15;

    slide.addShape(pptx.shapes.RECTANGLE, { x, y: 1, w: 3, h: 4, fill: { color: colors.white }, rectRadius: 0.08, shadow: { type: 'outer', blur: 3, offset: 1, angle: 45, opacity: 0.1 } });
    slide.addShape(pptx.shapes.RECTANGLE, { x, y: 1, w: 3, h: 0.65, fill: { color: colors.white }, rectRadius: 0.08 });
    slide.addShape(pptx.shapes.RECTANGLE, { x, y: 1.5, w: 3, h: 0.03, fill: { color: phase.color } });

    slide.addText(phase.title, { x, y: 1.05, w: 3, h: 0.3, fontSize: 12, bold: true, color: colors.darkNavy, fontFace: 'Arial', align: 'center' });
    slide.addText(phase.period, { x, y: 1.3, w: 3, h: 0.2, fontSize: 9, color: colors.charcoal, fontFace: 'Arial', align: 'center' });

    phase.items.forEach((item, j) => {
      slide.addShape(pptx.shapes.OVAL, { x: x + 0.2, y: 1.75 + j * 0.55, w: 0.12, h: 0.12, fill: { color: phase.color } });
      slide.addText(item, { x: x + 0.4, y: 1.65 + j * 0.55, w: 2.5, h: 0.5, fontSize: 9, color: colors.darkNavy, fontFace: 'Arial' });
    });

    // Status badge
    const badgeFill = phase.status === 'In Progress' ? phase.color : (phase.status === 'Planned' ? 'F5ECD9' : 'E8F4FC');
    const badgeText = phase.status === 'In Progress' ? colors.white : phase.color;
    slide.addShape(pptx.shapes.RECTANGLE, { x: x + 0.6, y: 4.5, w: 1.8, h: 0.35, fill: { color: badgeFill }, rectRadius: 0.03 });
    slide.addText(phase.status, { x: x + 0.6, y: 4.5, w: 1.8, h: 0.35, fontSize: 9, color: badgeText, fontFace: 'Arial', align: 'center', valign: 'middle' });
  });

  // ========== SLIDE 11: Key Learnings ==========
  slide = pptx.addSlide();
  slide.background = { color: colors.lightGray };

  // Header
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.8, fill: { color: colors.darkNavy } });
  slide.addText('Key Learnings', { x: 0.4, y: 0.2, w: 5, h: 0.5, fontSize: 22, bold: true, color: colors.white, fontFace: 'Arial' });

  // 6 learning cards - 2x3 grid
  const learnings = [
    { num: '1', title: 'Agentic Development is Production-Ready', desc: 'AI-assisted coding with Cursor and CC is mature enough for enterprise applications with proper guardrails.' },
    { num: '2', title: 'Junior Talent Can Be Rapidly Upskilled', desc: 'With proper tooling and mentorship, freshers become productive contributors within 2-3 months.' },
    { num: '3', title: 'AI Pair Programming Multiplies Output', desc: '3-5x velocity increase observed compared to traditional development methods.' },
    { num: '4', title: 'Documentation Discipline Prevents Chaos', desc: '38 ADRs ensured architectural consistency and prevented divergent implementations.' },
    { num: '5', title: 'Multi-Tenant from Day One', desc: 'Building enterprise features like data isolation early avoided costly retrofitting later.' },
    { num: '6', title: 'GitHub Projects Enables Visibility', desc: 'Roadmaps, milestones, and iterations provided stakeholder visibility throughout.' }
  ];

  learnings.forEach((learning, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.4 + col * 4.75;
    const y = 1 + row * 1.25;

    slide.addShape(pptx.shapes.RECTANGLE, { x, y, w: 4.6, h: 1.15, fill: { color: colors.white }, rectRadius: 0.06, shadow: { type: 'outer', blur: 2, offset: 1, angle: 45, opacity: 0.1 } });
    slide.addShape(pptx.shapes.OVAL, { x: x + 0.15, y: y + 0.15, w: 0.45, h: 0.45, fill: { color: colors.teal } });
    slide.addText(learning.num, { x: x + 0.15, y: y + 0.15, w: 0.45, h: 0.45, fontSize: 14, bold: true, color: colors.white, fontFace: 'Arial', align: 'center', valign: 'middle' });
    slide.addText(learning.title, { x: x + 0.7, y: y + 0.1, w: 3.75, h: 0.35, fontSize: 10, bold: true, color: colors.darkNavy, fontFace: 'Arial' });
    slide.addText(learning.desc, { x: x + 0.7, y: y + 0.45, w: 3.75, h: 0.6, fontSize: 8, color: colors.charcoal, fontFace: 'Arial' });
  });

  // ========== SLIDE 12: Call to Action ==========
  slide = pptx.addSlide();
  slide.background = { color: colors.darkNavy };

  // Title
  slide.addText("What's Next?", { x: 0.5, y: 0.8, w: 9, h: 0.6, fontSize: 30, bold: true, color: colors.white, fontFace: 'Arial', align: 'center' });

  // CTA cards
  const ctas = [
    { title: 'Beta Engagements', desc: 'Seeking opportunities to deploy on live cloud assessment projects' },
    { title: 'Methodology Adoption', desc: 'Share agentic development practices across the organization' },
    { title: 'Knowledge Transfer', desc: 'Available for sessions on AI-assisted development tooling' }
  ];

  ctas.forEach((cta, i) => {
    const x = 0.8 + i * 3;
    slide.addShape(pptx.shapes.RECTANGLE, { x, y: 1.6, w: 2.7, h: 1.4, fill: { color: '3D5066' }, rectRadius: 0.08, line: { color: '5A6E80', pt: 0.5 } });
    slide.addText(cta.title, { x, y: 1.75, w: 2.7, h: 0.35, fontSize: 12, bold: true, color: colors.gold, fontFace: 'Arial', align: 'center' });
    slide.addText(cta.desc, { x: x + 0.15, y: 2.15, w: 2.4, h: 0.75, fontSize: 9, color: colors.white, fontFace: 'Arial', align: 'center' });
  });

  // Questions section
  slide.addText('Questions?', { x: 0.5, y: 3.5, w: 9, h: 0.5, fontSize: 20, bold: true, color: colors.teal, fontFace: 'Arial', align: 'center' });
  slide.addText('Thank you for your time and attention', { x: 0.5, y: 4, w: 9, h: 0.3, fontSize: 11, color: colors.mediumGray, fontFace: 'Arial', align: 'center' });

  // Accent line
  slide.addShape(pptx.shapes.RECTANGLE, { x: 4.3, y: 4.5, w: 1.4, h: 0.05, fill: { color: colors.teal } });

  // ========== APPENDIX A: Team Highlights ==========
  slide = pptx.addSlide();
  slide.background = { color: colors.lightGray };

  // Header
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.9, fill: { color: colors.charcoal } });
  slide.addText('APPENDIX A', { x: 0.4, y: 0.15, w: 2, h: 0.25, fontSize: 9, color: colors.gold, fontFace: 'Arial' });
  slide.addText('Team Member Highlights', { x: 0.4, y: 0.4, w: 5, h: 0.4, fontSize: 20, bold: true, color: colors.white, fontFace: 'Arial' });

  // Placeholder cards
  for (let i = 0; i < 3; i++) {
    const x = 0.5 + i * 3.1;
    slide.addShape(pptx.shapes.RECTANGLE, { x, y: 1.2, w: 2.9, h: 3.3, fill: { color: colors.white }, rectRadius: 0.08, line: { color: colors.mediumGray, pt: 1, dashType: 'dash' } });
    slide.addText(`[Team Member ${i + 1}]`, { x, y: 1.8, w: 2.9, h: 0.4, fontSize: 12, bold: true, color: colors.charcoal, fontFace: 'Arial', align: 'center' });
    slide.addText('Role transformation story\n\nKey achievements\n\nTestimonial quote', { x: x + 0.2, y: 2.4, w: 2.5, h: 1.8, fontSize: 10, color: colors.mediumGray, fontFace: 'Arial', align: 'center' });
  }

  // ========== APPENDIX B: Executive Sponsor ==========
  slide = pptx.addSlide();
  slide.background = { color: colors.lightGray };

  // Header
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.9, fill: { color: colors.charcoal } });
  slide.addText('APPENDIX B', { x: 0.4, y: 0.15, w: 2, h: 0.25, fontSize: 9, color: colors.gold, fontFace: 'Arial' });
  slide.addText('Executive Sponsor Validation', { x: 0.4, y: 0.4, w: 6, h: 0.4, fontSize: 20, bold: true, color: colors.white, fontFace: 'Arial' });

  // Quote box
  slide.addShape(pptx.shapes.RECTANGLE, { x: 1, y: 1.5, w: 8, h: 2.5, fill: { color: colors.white }, rectRadius: 0.08, shadow: { type: 'outer', blur: 3, offset: 1, angle: 45, opacity: 0.1 } });
  slide.addShape(pptx.shapes.RECTANGLE, { x: 1, y: 1.5, w: 0.08, h: 2.5, fill: { color: colors.gold } });

  slide.addText('"[Placeholder for executive sponsor quote validating the project\'s impact, team growth, and strategic value to the organization.]"', {
    x: 1.3, y: 1.7, w: 7.5, h: 1.3, fontSize: 14, italic: true, color: colors.darkNavy, fontFace: 'Arial'
  });

  // Attribution placeholder
  slide.addShape(pptx.shapes.OVAL, { x: 1.3, y: 3.2, w: 0.7, h: 0.7, fill: { color: colors.mediumGray }, line: { color: colors.charcoal, pt: 1, dashType: 'dash' } });
  slide.addText('[Executive Name]', { x: 2.2, y: 3.2, w: 3, h: 0.35, fontSize: 11, bold: true, color: colors.darkNavy, fontFace: 'Arial' });
  slide.addText('[Title, Organization]', { x: 2.2, y: 3.5, w: 3, h: 0.3, fontSize: 10, color: colors.charcoal, fontFace: 'Arial' });

  // Note
  slide.addText('To be added after executive review and approval', { x: 1, y: 4.3, w: 8, h: 0.3, fontSize: 9, italic: true, color: colors.mediumGray, fontFace: 'Arial', align: 'center' });

  // Save presentation
  const outputPath = '/Users/chocka/CursorProjects/migrate-ui-orchestrator/workspace/AI_Force_Assess_Executive_Briefing.pptx';
  await pptx.writeFile({ fileName: outputPath });
  console.log(`\nPresentation saved to: ${outputPath}`);
  console.log('\nSlide Summary:');
  console.log('  1. Title');
  console.log('  2. The Challenge');
  console.log('  3. The Solution');
  console.log('  4. The Innovation');
  console.log('  5. Team Transformation');
  console.log('  6. By The Numbers (with velocity chart)');
  console.log('  7. Cost Efficiency');
  console.log('  8. Architecture Overview');
  console.log('  9. Live Demo');
  console.log('  10. Roadmap');
  console.log('  11. Key Learnings');
  console.log('  12. Call to Action');
  console.log('  A1. Team Member Highlights (Appendix - Placeholder)');
  console.log('  A2. Executive Sponsor (Appendix - Placeholder)');
}

createPresentation().catch(console.error);
