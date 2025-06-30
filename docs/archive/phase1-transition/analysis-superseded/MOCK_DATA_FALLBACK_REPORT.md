# Mock Data Fallback Report

This document catalogs all instances where the application falls back to using mock or demo data when real data is unavailable or when in a demo mode. This helps in understanding where the application might need better error handling or data loading mechanisms.

## Table of Contents
- [Authentication](#authentication)
- [Admin Dashboard](#admin-dashboard)
- [Discovery Flow](#discovery-flow)
- [Agent Learning](#agent-learning)
- [User Management](#user-management)
- [Feedback System](#feedback-system)
- [Data Cleansing](#data-cleansing)

## Authentication

### Login Page
- **File**: `/src/pages/Login.tsx`
- **Fallback Type**: Hardcoded demo credentials
- **Description**: Contains demo credentials for testing purposes that match the database seed.
- **Impact**: Allows demo users to log in without real credentials.
- **Trigger Condition**: When users enter the demo credentials.

## Admin Dashboard

### Dashboard Statistics
- **File**: `/src/pages/admin/AdminDashboard.tsx`
- **Fallback Type**: Demo data on API failure
- **Description**: Falls back to demo statistics when the API endpoint is unavailable.
- **Impact**: Dashboard remains functional with sample data.
- **Trigger Condition**: API call failure or network issues.

### Client Details
- **File**: `/src/pages/admin/ClientDetails.tsx`
- **Fallback Type**: Demo client data
- **Description**: Shows demo client data when real data cannot be fetched.
- **Impact**: UI remains populated with sample client information.
- **Trigger Condition**: Failed API call or missing client data.

### Engagement Details
- **File**: `/src/pages/admin/EngagementDetails.tsx`
- **Fallback Type**: Demo engagement data
- **Description**: Displays sample engagement data when real data is unavailable.
- **Impact**: Maintains UI functionality with placeholder data.
- **Trigger Condition**: API failure or missing engagement data.

## Discovery Flow

### Flow Creation
- **File**: `/src/pages/discovery/DiscoveryFlowV2.tsx`
- **Fallback Type**: Demo flow data
- **Description**: Creates a demo flow with sample database information.
- **Impact**: Allows users to explore the discovery flow without real data.
- **Trigger Condition**: When creating a new flow in demo mode.

### Enhanced Dashboard
- **File**: `/src/pages/discovery/EnhancedDiscoveryDashboard.tsx`
- **Fallback Type**: Fallback data on error
- **Description**: Provides fallback data to prevent UI breakage.
- **Impact**: Maintains UI stability during data loading issues.
- **Trigger Condition**: Data loading errors.

## Agent Learning

### Learning Insights
- **File**: `/src/components/discovery/AgentLearningInsights.tsx`
- **Fallback Type**: Demo learning data
- **Description**: Provides sample learning data when the agent learning service is unavailable.
- **Impact**: Demonstrates functionality without real agent learning.
- **Trigger Condition**: Service unavailability or errors.

### Field Mapping
- **File**: `/src/components/discovery/AgentLearningInsights.tsx`
- **Fallback Type**: Simulated learning updates
- **Description**: Updates demo data to simulate learning from user feedback.
- **Impact**: Shows how the system would learn without backend integration.
- **Trigger Condition**: User interaction with field mapping.

## User Management

### User Approvals
- **File**: `/src/components/admin/user-approvals/UserApprovalsMain.tsx`
- **Fallback Type**: Demo user data
- **Description**: Shows sample pending and active users when real data is unavailable.
- **Impact**: Allows testing of user management features.
- **Trigger Condition**: API failures or missing user data.

### Access Management
- **File**: `/src/components/admin/user-approvals/UserAccessManagement.tsx`
- **Fallback Type**: Demo access data
- **Description**: Provides sample client and engagement data for access management.
- **Impact**: Enables testing of access control features.
- **Trigger Condition**: Missing or failed data loading.

## Feedback System

### Feedback View
- **File**: `/src/pages/FeedbackView.tsx`
- **Fallback Type**: Demo feedback data
- **Description**: Shows sample feedback when real data is unavailable.
- **Impact**: Maintains UI functionality with sample feedback.
- **Trigger Condition**: API failures or missing feedback data.

## Data Cleansing

### Data Samples
- **File**: `/src/pages/discovery/DataCleansing.tsx`
- **Fallback Type**: Empty arrays as fallback
- **Description**: Uses empty arrays when no data is available for cleansing.
- **Impact**: Prevents errors in the data cleansing interface.
- **Trigger Condition**: Missing or empty data.

## Recommendations

1. **Error Handling**: Improve error handling to provide better user feedback when falling back to demo data.
2. **Feature Flags**: Consider using feature flags to control demo data visibility.
3. **Documentation**: Document the expected data formats and fallback behaviors.
4. **Testing**: Add tests to verify fallback behaviors work as expected.
5. **Monitoring**: Implement monitoring to track when fallbacks are triggered in production.

## Implementation Notes

- The `useUserType` hook controls whether demo data should be shown via the `should_see_mock_data_only` flag.
- Demo data is often provided through dedicated demo data services or hardcoded in components.
- Fallback mechanisms are crucial for development and demo purposes but should be clearly indicated in the UI.

---
*Last Updated: 2025-06-27*
