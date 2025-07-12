# UI Components Design for Asset Enrichment

## Component Architecture Overview

The asset enrichment UI integrates seamlessly with existing discovery flow pages by enhancing current components and adding new enrichment-specific interfaces. All user interactions follow the established agent-ui-bridge pattern using the AgentClarificationPanel for MCQ and short text inputs.

## Enhanced Component Hierarchy

```
Discovery Page Layout
├── Main Content Area (xl:col-span-3)
│   ├── Existing Core Components
│   ├── EnrichmentOverviewCard (NEW)
│   ├── AssetEnrichmentTable (NEW)
│   └── PhaseSpecificEnrichmentPanels (NEW)
└── Agent Interaction Area (xl:col-span-1)
    ├── AgentClarificationPanel (ENHANCED)
    ├── AgentInsightsSection (ENHANCED)
    ├── EnrichmentProgressCard (NEW)
    └── EnrichmentCompletionGating (NEW)
```

## Core Enrichment Components

### **1. EnrichmentOverviewCard**

**Purpose:** Provides high-level enrichment status and progress across all phases.

```tsx
interface EnrichmentOverviewProps {
  flowId: string;
  overallStatus: OverallEnrichmentStatus;
  onRefreshStatus: () => void;
}

const EnrichmentOverviewCard: React.FC<EnrichmentOverviewProps> = ({
  flowId,
  overallStatus,
  onRefreshStatus
}) => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* Header with progress */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <Brain className="h-6 w-6 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Asset Enrichment Progress
          </h3>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-2xl font-bold text-blue-600">
            {overallStatus.overall_completion}%
          </span>
          <button
            onClick={onRefreshStatus}
            className="p-1 text-gray-400 hover:text-gray-600"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${overallStatus.overall_completion}%` }}
        />
      </div>

      {/* Phase breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <EnrichmentPhaseCard
          title="Classification"
          icon={<Tags className="h-5 w-5" />}
          status={overallStatus.phase_status.classification}
          color="blue"
        />
        <EnrichmentPhaseCard
          title="Business Context"
          icon={<Building className="h-5 w-5" />}
          status={overallStatus.phase_status.business_context}
          color="green"
        />
        <EnrichmentPhaseCard
          title="Risk Assessment"
          icon={<Shield className="h-5 w-5" />}
          status={overallStatus.phase_status.risk_assessment}
          color="orange"
        />
      </div>

      {/* 6R Readiness indicator */}
      <div className="mt-4 p-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-md border border-blue-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Target className="h-5 w-5 text-blue-600" />
            <span className="text-sm font-medium text-blue-900">
              6R Strategy Readiness
            </span>
          </div>
          <span className="text-lg font-bold text-blue-600">
            {overallStatus.readiness_for_6r}%
          </span>
        </div>
        <p className="text-xs text-blue-700 mt-1">
          Higher enrichment completeness leads to more accurate migration recommendations
        </p>
      </div>
    </div>
  );
};
```

### **2. AssetEnrichmentTable**

**Purpose:** Displays assets with their enrichment status, missing fields, and allows quick access to enrichment actions.

```tsx
interface AssetEnrichmentTableProps {
  assets: EnrichedAsset[];
  enrichmentFields: string[];
  onAssetSelect: (assetId: string) => void;
  onBulkAction: (assetIds: string[], action: string) => void;
}

const AssetEnrichmentTable: React.FC<AssetEnrichmentTableProps> = ({
  assets,
  enrichmentFields,
  onAssetSelect,
  onBulkAction
}) => {
  const [selectedAssets, setSelectedAssets] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState<'name' | 'enrichment_score' | 'business_value'>('enrichment_score');

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      {/* Table header with controls */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">
            Asset Enrichment Status
          </h3>
          <div className="flex items-center space-x-3">
            {/* Sort controls */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="text-sm border border-gray-300 rounded px-2 py-1"
            >
              <option value="enrichment_score">Sort by Enrichment</option>
              <option value="business_value">Sort by Business Value</option>
              <option value="name">Sort by Name</option>
            </select>
            
            {/* Bulk actions */}
            {selectedAssets.length > 0 && (
              <BulkActionDropdown
                selectedCount={selectedAssets.length}
                onAction={(action) => onBulkAction(selectedAssets, action)}
              />
            )}
          </div>
        </div>
      </div>

      {/* Table content */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="w-8 px-3 py-3">
                <input
                  type="checkbox"
                  checked={selectedAssets.length === assets.length}
                  onChange={(e) =>
                    setSelectedAssets(
                      e.target.checked ? assets.map(a => a.id) : []
                    )
                  }
                />
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Asset
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Enrichment Score
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Missing Fields
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Business Value
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {assets.map((asset) => (
              <AssetEnrichmentRow
                key={asset.id}
                asset={asset}
                isSelected={selectedAssets.includes(asset.id)}
                onSelect={(selected) => 
                  setSelectedAssets(prev => 
                    selected 
                      ? [...prev, asset.id]
                      : prev.filter(id => id !== asset.id)
                  )
                }
                onAssetClick={() => onAssetSelect(asset.id)}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const AssetEnrichmentRow: React.FC<{
  asset: EnrichedAsset;
  isSelected: boolean;
  onSelect: (selected: boolean) => void;
  onAssetClick: () => void;
}> = ({ asset, isSelected, onSelect, onAssetClick }) => {
  const enrichmentScore = asset.enrichment_score || 0;
  const missingFields = asset.missing_critical_fields || [];
  
  return (
    <tr className="hover:bg-gray-50">
      <td className="px-3 py-4">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={(e) => onSelect(e.target.checked)}
        />
      </td>
      
      <td className="px-6 py-4">
        <div className="flex items-center">
          <div>
            <button
              onClick={onAssetClick}
              className="text-sm font-medium text-blue-600 hover:text-blue-800"
            >
              {asset.name}
            </button>
            {asset.hostname && (
              <p className="text-xs text-gray-500">{asset.hostname}</p>
            )}
          </div>
        </div>
      </td>
      
      <td className="px-6 py-4">
        <AssetTypebadge assetType={asset.asset_type} subtype={asset.asset_subtype} />
      </td>
      
      <td className="px-6 py-4">
        <EnrichmentScoreBadge score={enrichmentScore} />
      </td>
      
      <td className="px-6 py-4">
        <MissingFieldsIndicator fields={missingFields} />
      </td>
      
      <td className="px-6 py-4">
        <BusinessValueIndicator value={asset.business_value_score} />
      </td>
      
      <td className="px-6 py-4">
        <button
          onClick={onAssetClick}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          Enrich
        </button>
      </td>
    </tr>
  );
};
```

### **3. Enhanced AgentClarificationPanel**

**Purpose:** Extended to handle enrichment-specific question types with better context display.

```tsx
interface EnhancedAgentClarificationPanelProps {
  pageContext: 'asset-classification' | 'business-context' | 'risk-assessment';
  questionTypes?: string[];
  onQuestionAnswered?: (questionId: string, response: any) => void;
}

const EnhancedAgentClarificationPanel: React.FC<EnhancedAgentClarificationPanelProps> = ({
  pageContext,
  questionTypes = [],
  onQuestionAnswered
}) => {
  const [questions, setQuestions] = useState<AgentQuestion[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [responses, setResponses] = useState<Record<string, any>>({});

  // Enhanced question rendering based on type
  const renderQuestionContent = (question: AgentQuestion) => {
    switch (question.question_type) {
      case 'asset_classification':
        return <AssetClassificationQuestion question={question} />;
      case 'business_value_assessment':
        return <BusinessValueQuestion question={question} />;
      case 'compliance_requirement':
        return <ComplianceRequirementQuestion question={question} />;
      default:
        return <StandardQuestion question={question} />;
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Brain className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold">Asset Intelligence</h3>
        </div>
        {questions.length > 1 && (
          <span className="text-sm text-gray-500">
            {currentQuestionIndex + 1} of {questions.length}
          </span>
        )}
      </div>

      {questions.length > 0 ? (
        <div className="space-y-4">
          {/* Progress indicator for multiple questions */}
          {questions.length > 1 && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${((currentQuestionIndex + 1) / questions.length) * 100}%` }}
              />
            </div>
          )}

          {/* Current question */}
          <div className="border border-gray-200 rounded-lg p-4">
            {renderQuestionContent(questions[currentQuestionIndex])}
          </div>

          {/* Navigation */}
          <div className="flex justify-between">
            <button
              onClick={() => setCurrentQuestionIndex(Math.max(0, currentQuestionIndex - 1))}
              disabled={currentQuestionIndex === 0}
              className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setCurrentQuestionIndex(Math.min(questions.length - 1, currentQuestionIndex + 1))}
              disabled={currentQuestionIndex === questions.length - 1}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <Brain className="h-12 w-12 mx-auto mb-3 text-gray-300" />
          <p>AI agents are analyzing your assets...</p>
          <p className="text-sm mt-1">Questions will appear here if clarification is needed</p>
        </div>
      )}
    </div>
  );
};
```

### **4. Enrichment-Specific Question Components**

**Purpose:** Specialized question components for different enrichment types with rich context display.

```tsx
const AssetClassificationQuestion: React.FC<{ question: AgentQuestion }> = ({ question }) => {
  const [selectedOption, setSelectedOption] = useState<string>('');
  const context = question.context;

  return (
    <div className="space-y-4">
      {/* Question header */}
      <div className="flex items-start space-x-3">
        <Server className="h-5 w-5 text-blue-600 mt-1" />
        <div className="flex-1">
          <h4 className="font-medium text-gray-900">{question.title}</h4>
          <p className="text-sm text-gray-600 mt-1">{question.question}</p>
        </div>
      </div>

      {/* Asset context card */}
      <div className="bg-gray-50 rounded-lg p-3 border">
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="font-medium text-gray-700">Asset:</span>
            <span className="ml-2 text-gray-900">{context.asset_name}</span>
          </div>
          {context.hostname && (
            <div>
              <span className="font-medium text-gray-700">Hostname:</span>
              <span className="ml-2 text-gray-900">{context.hostname}</span>
            </div>
          )}
          {context.operating_system && (
            <div>
              <span className="font-medium text-gray-700">OS:</span>
              <span className="ml-2 text-gray-900">{context.operating_system}</span>
            </div>
          )}
          {context.detected_patterns && context.detected_patterns.length > 0 && (
            <div className="col-span-2">
              <span className="font-medium text-gray-700">Detected patterns:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {context.detected_patterns.map((pattern: string) => (
                  <span key={pattern} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                    {pattern}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* AI suggestion */}
      {context.ai_suggestion && (
        <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
          <div className="flex items-center space-x-2 mb-2">
            <Brain className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-900">AI Suggestion</span>
            <ConfidenceBadge confidence={context.confidence} />
          </div>
          <p className="text-sm text-blue-800">{context.ai_suggestion}</p>
        </div>
      )}

      {/* Answer options */}
      <div className="space-y-2">
        {question.options?.map((option) => (
          <label key={option} className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
            <input
              type="radio"
              name={`question-${question.id}`}
              value={option}
              checked={selectedOption === option}
              onChange={(e) => setSelectedOption(e.target.value)}
              className="text-blue-600"
            />
            <span className="text-sm text-gray-900">{option}</span>
            {context.ai_suggestion === option && (
              <Badge variant="outline" className="ml-auto text-xs">Recommended</Badge>
            )}
          </label>
        ))}
      </div>

      {/* Submit button */}
      <button
        onClick={() => handleSubmitResponse(question.id, selectedOption)}
        disabled={!selectedOption}
        className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-700"
      >
        Submit Response
      </button>
    </div>
  );
};

const BusinessValueQuestion: React.FC<{ question: AgentQuestion }> = ({ question }) => {
  const [selectedValue, setSelectedValue] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const context = question.context;

  return (
    <div className="space-y-4">
      {/* Question header */}
      <div className="flex items-start space-x-3">
        <Building className="h-5 w-5 text-green-600 mt-1" />
        <div className="flex-1">
          <h4 className="font-medium text-gray-900">{question.title}</h4>
          <p className="text-sm text-gray-600 mt-1">{question.question}</p>
        </div>
      </div>

      {/* Application context */}
      <div className="bg-gray-50 rounded-lg p-3 border">
        <div className="space-y-2 text-sm">
          <div>
            <span className="font-medium text-gray-700">Application:</span>
            <span className="ml-2 text-gray-900">{context.application_name}</span>
          </div>
          {context.detected_patterns && context.detected_patterns.length > 0 && (
            <div>
              <span className="font-medium text-gray-700">Detected indicators:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {context.detected_patterns.map((pattern: string) => (
                  <span key={pattern} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                    {pattern}
                  </span>
                ))}
              </div>
            </div>
          )}
          {context.ai_reasoning && (
            <div>
              <span className="font-medium text-gray-700">AI Analysis:</span>
              <p className="ml-2 text-gray-900 mt-1">{context.ai_reasoning}</p>
            </div>
          )}
        </div>
      </div>

      {/* Value options with descriptions */}
      <div className="space-y-2">
        {question.options?.map((option) => (
          <label key={option} className="flex items-start space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
            <input
              type="radio"
              name={`question-${question.id}`}
              value={option}
              checked={selectedValue === option}
              onChange={(e) => setSelectedValue(e.target.value)}
              className="text-green-600 mt-1"
            />
            <div className="flex-1">
              <span className="text-sm font-medium text-gray-900">{option}</span>
              <p className="text-xs text-gray-500 mt-1">
                {getBusinessValueDescription(option)}
              </p>
            </div>
            {context.ai_suggestion?.includes(option.split(' ')[0]) && (
              <Badge variant="outline" className="text-xs">Suggested</Badge>
            )}
          </label>
        ))}
      </div>

      {/* Optional notes */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Additional Notes (Optional)
        </label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Any additional context about this application's business importance..."
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
          rows={2}
          maxLength={200}
        />
        <p className="text-xs text-gray-500 mt-1">{notes.length}/200 characters</p>
      </div>

      {/* Submit */}
      <button
        onClick={() => handleSubmitResponse(question.id, { value: selectedValue, notes })}
        disabled={!selectedValue}
        className="w-full px-4 py-2 bg-green-600 text-white rounded-lg disabled:opacity-50 hover:bg-green-700"
      >
        Submit Assessment
      </button>
    </div>
  );
};
```

### **5. EnrichmentProgressCard**

**Purpose:** Shows current phase enrichment progress and blocking issues.

```tsx
interface EnrichmentProgressCardProps {
  phase: 'classification' | 'business_context' | 'risk_assessment';
  progress: number;
  blockers?: string[];
  criticalApplications?: number;
  highRiskAssets?: number;
}

const EnrichmentProgressCard: React.FC<EnrichmentProgressCardProps> = ({
  phase,
  progress,
  blockers = [],
  criticalApplications,
  highRiskAssets
}) => {
  const phaseConfig = {
    classification: {
      title: 'Asset Classification',
      icon: <Tags className="h-5 w-5" />,
      color: 'blue',
      description: 'Classifying asset types and subtypes'
    },
    business_context: {
      title: 'Business Context',
      icon: <Building className="h-5 w-5" />,
      color: 'green',
      description: 'Collecting business value and requirements'
    },
    risk_assessment: {
      title: 'Risk Assessment',
      icon: <Shield className="h-5 w-5" />,
      color: 'orange',
      description: 'Analyzing compliance and operational risks'
    }
  };

  const config = phaseConfig[phase];

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      {/* Header */}
      <div className="flex items-center space-x-3 mb-3">
        <div className={`p-2 bg-${config.color}-100 rounded-lg`}>
          {config.icon}
        </div>
        <div>
          <h3 className="font-medium text-gray-900">{config.title}</h3>
          <p className="text-sm text-gray-500">{config.description}</p>
        </div>
      </div>

      {/* Progress */}
      <div className="mb-3">
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm font-medium text-gray-700">Progress</span>
          <span className="text-sm font-bold text-gray-900">{progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`bg-${config.color}-600 h-2 rounded-full transition-all duration-300`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Key metrics */}
      {criticalApplications && (
        <div className="flex justify-between items-center py-2 border-t border-gray-100">
          <span className="text-sm text-gray-600">Critical Applications</span>
          <span className="text-sm font-medium text-gray-900">{criticalApplications}</span>
        </div>
      )}
      
      {highRiskAssets && (
        <div className="flex justify-between items-center py-2 border-t border-gray-100">
          <span className="text-sm text-gray-600">High Risk Assets</span>
          <span className="text-sm font-medium text-orange-600">{highRiskAssets}</span>
        </div>
      )}

      {/* Blockers */}
      {blockers.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <div className="flex items-center space-x-2 mb-2">
            <AlertCircle className="h-4 w-4 text-amber-500" />
            <span className="text-sm font-medium text-amber-700">Blockers</span>
          </div>
          <ul className="space-y-1">
            {blockers.map((blocker, index) => (
              <li key={index} className="text-xs text-amber-600">
                • {blocker}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
```

## Page-Specific Integration

### **Data Cleansing Page Enhancement**

```tsx
const EnhancedDataCleansingPage = () => {
  const { flowId } = useParams();
  const { enrichmentStatus, classificationQuestions, refreshStatus } = useAssetClassificationEnrichment(flowId);

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 overflow-y-auto">
        <ContextBreadcrumbs />
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            
            {/* Main content area */}
            <div className="xl:col-span-3 space-y-6">
              
              {/* Existing data cleansing components */}
              <DataQualityAssessment />
              <IssueResolutionPanel />
              
              {/* NEW: Enrichment overview */}
              <EnrichmentOverviewCard 
                flowId={flowId}
                overallStatus={enrichmentStatus.overall}
                onRefreshStatus={refreshStatus}
              />
              
              {/* NEW: Asset classification status */}
              <AssetEnrichmentTable 
                assets={enrichmentStatus.assets}
                enrichmentFields={['asset_type', 'asset_subtype', 'business_criticality']}
                onAssetSelect={(assetId) => handleAssetSelect(assetId)}
                onBulkAction={(assetIds, action) => handleBulkClassification(assetIds, action)}
              />
              
            </div>
            
            {/* Agent interaction area */}
            <div className="xl:col-span-1 space-y-6">
              
              {/* Enhanced agent panel for classification questions */}
              <EnhancedAgentClarificationPanel 
                pageContext="asset-classification"
                questionTypes={['asset_type_confirmation', 'missing_field_clarification']}
                onQuestionAnswered={handleQuestionAnswered}
              />
              
              <AgentInsightsSection category="classification" />
              
              {/* Progress tracking */}
              <EnrichmentProgressCard 
                phase="classification"
                progress={enrichmentStatus.classification.completion_percentage}
                blockers={enrichmentStatus.classification.blockers}
              />
              
              {/* Flow progression gating */}
              <EnrichmentCompletionGating 
                phase="classification"
                canProceed={enrichmentStatus.classification.can_proceed}
                requirements={enrichmentStatus.classification.requirements}
                onProceed={() => navigateToNextPhase()}
              />
              
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
```

## Integration with Existing Agent-UI-Bridge

### **Enhanced Question Handling**

```tsx
const useEnhancedAgentQuestions = (pageContext: string) => {
  const [questions, setQuestions] = useState<AgentQuestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const pollForQuestions = useCallback(async () => {
    try {
      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_STATUS, {
        method: 'GET',
        headers: {
          'X-Page-Context': pageContext
        }
      });

      if (response?.questions) {
        // Filter questions by page context and enrichment types
        const relevantQuestions = response.questions.filter(q => 
          q.page === pageContext || 
          q.question_type.includes('enrichment') ||
          q.question_type.includes(pageContext.replace('-', '_'))
        );
        
        setQuestions(relevantQuestions);
      }
    } catch (error) {
      console.error('Error polling for enrichment questions:', error);
    }
  }, [pageContext]);

  const submitResponse = useCallback(async (questionId: string, response: any) => {
    setIsLoading(true);
    try {
      await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_CLARIFICATION, {
        method: 'POST',
        body: JSON.stringify({
          question_id: questionId,
          response: response,
          page_context: pageContext,
          enrichment_context: true  // Flag for enrichment learning
        })
      });

      // Remove answered question and poll for new ones
      setQuestions(prev => prev.filter(q => q.id !== questionId));
      await pollForQuestions();
    } catch (error) {
      console.error('Error submitting enrichment response:', error);
    } finally {
      setIsLoading(false);
    }
  }, [pageContext, pollForQuestions]);

  return {
    questions,
    isLoading,
    submitResponse,
    refreshQuestions: pollForQuestions
  };
};
```

---

*Next: [05_database_schema.md](05_database_schema.md)*