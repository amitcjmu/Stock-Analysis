# Field Mapping Confidence Score Analysis

## Overview
This document analyzes how `field_mapping_confidence` scores are being used throughout the codebase based on the investigation conducted on July 5, 2025.

## Key Findings

### 1. Where Confidence Scores are Stored

#### Model Definition
- **Location**: `backend/app/models/unified_discovery_flow_state.py`
- **Storage Structure**:
  ```python
  field_mappings: Dict[str, Any] = Field(default_factory=lambda: {
      "mappings": {},
      "confidence_scores": {},  # Individual field confidence scores
      "unmapped_fields": [],
      "validation_results": {},
      "agent_insights": {}
  })
  ```

#### Success Criteria
- **Default Threshold**: 0.8 (80%)
- **Defined in**: `success_criteria["field_mapping"]["field_mappings_confidence"]`

### 2. How Confidence Scores are Calculated

#### Scoring Algorithm
- **Location**: `backend/app/services/confidence/scoring_algorithms.py`
- **Method**: `field_mapping_confidence()`
- **Calculation**:
  ```python
  # Base mapping rate (70% max)
  mapping_rate = mapped_fields / total_fields
  base_confidence = mapping_rate * 70
  
  # Quality bonus from individual mapping confidences (30% max)
  avg_mapping_confidence = mean(individual_confidences)
  quality_bonus = avg_mapping_confidence * 30
  
  # Total: 0-100%
  return min(100.0, base_confidence + quality_bonus)
  ```

### 3. Where Confidence Scores are Used

#### A. Phase Validation (Decision Logic)
- **Location**: `backend/app/services/crewai_flows/handlers/flow_execution_handler.py`
- **Method**: `validate_phase_success()`
- **Logic**:
  ```python
  # Calculate average confidence from all field mappings
  avg_confidence = sum(confidence_scores.values()) / len(confidence_scores)
  
  # Check if meets threshold
  confidence_met = avg_confidence >= 0.8  # 80% threshold
  
  # Must also check unmapped fields and validation
  return confidence_met and unmapped_met and validation_passed
  ```

#### B. Flow State Validation
- **Location**: `backend/app/models/unified_discovery_flow_state.py`
- **Method**: `validate_phase_success("field_mapping")`
- **Purpose**: Determines if the field mapping phase is complete and successful

#### C. Planning & Coordination
- **Location**: Multiple handler files
- **Usage**: Success criteria includes `"field_mappings_confidence > 0.8"`
- **Impact**: Used to determine if flow can proceed to next phase

### 4. UI Display of Confidence Scores

#### Field Mapping Tab
- **Location**: `src/components/discovery/attribute-mapping/FieldMappingsTab.tsx`
- **Display**:
  ```tsx
  <span className={`px-2 py-1 text-xs rounded-full ${getConfidenceColor(mapping.confidence)}`}>
    {Math.round(mapping.confidence * 100)}% confidence
  </span>
  ```
- **Color Coding**:
  - Green: >= 80%
  - Yellow: >= 60%
  - Red: < 60%

#### Confidence Score Indicator Component
- **Location**: `src/components/assessment/ConfidenceScoreIndicator.tsx`
- **Features**:
  - Visual progress bar
  - Color-coded badges
  - Breakdown display for multiple factors
  - Size variants (small, medium, large)

### 5. Current Usage Status

#### Active Usage
1. **Phase Validation**: ✅ Actively used to determine if field mapping phase passes
2. **UI Display**: ✅ Individual field mapping confidences are displayed
3. **Flow Control**: ✅ Prevents progression if confidence threshold not met

#### Passive/Storage Only
1. **Agent Results**: Stored but not actively queried after phase completion
2. **Historical Analysis**: No evidence of historical confidence tracking
3. **Learning/Improvement**: No evidence of using past confidence scores for learning

## Conclusion

**Field mapping confidence scores are ACTIVELY USED for:**
1. **Quality Gate**: Enforcing an 80% confidence threshold before allowing flow progression
2. **User Feedback**: Displaying individual mapping confidence in the UI
3. **Decision Making**: Determining if the field mapping phase is successful

**The data is NOT just stored - it has real impact on:**
- Whether users can proceed to the data cleansing phase
- Which mappings are highlighted as high/low confidence
- Overall flow success criteria

## Recommendations

1. **Consider Adjustable Thresholds**: The 80% threshold is hard-coded; consider making it configurable per client/engagement
2. **Historical Tracking**: Implement tracking of confidence scores over time to identify improvement areas
3. **Learning Integration**: Use historical confidence data to improve future mapping suggestions
4. **Detailed Breakdown**: The UI shows overall confidence but could benefit from showing contributing factors