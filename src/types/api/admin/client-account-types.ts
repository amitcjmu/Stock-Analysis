/**
 * Client Account Management API Types
 * 
 * Type definitions for client account management including account creation,
 * subscription management, billing, and account lifecycle operations.
 * 
 * Generated with CC for modular admin type organization.
 */

import {
  BaseApiRequest,
  BaseApiResponse,
  ListRequest,
  ListResponse,
  GetRequest,
  GetResponse,
  CreateRequest,
  CreateResponse,
  UpdateRequest,
  UpdateResponse
} from '../shared';

// Client Account Creation APIs
export interface CreateClientAccountRequest extends CreateRequest<ClientAccountData> {
  data: ClientAccountData;
  adminUser: AdminUserData;
  subscriptionPlan?: string;
  billingInfo?: BillingInformation;
  setupConfiguration?: AccountSetupConfig;
}

export interface CreateClientAccountResponse extends CreateResponse<ClientAccount> {
  data: ClientAccount;
  accountId: string;
  adminUser: User;
  subscriptionActive: boolean;
  setupCompleted: boolean;
}

// Client Account Retrieval APIs
export interface GetClientAccountRequest extends GetRequest {
  accountId: string;
  includeUsers?: boolean;
  includeEngagements?: boolean;
  includeSubscription?: boolean;
  includeBilling?: boolean;
  includeUsage?: boolean;
}

export interface GetClientAccountResponse extends GetResponse<ClientAccount> {
  data: ClientAccount;
  users: AccountUser[];
  engagements: AccountEngagement[];
  subscription: SubscriptionDetails;
  billing: BillingDetails;
  usage: UsageMetrics;
}

// Client Account Listing APIs
export interface ListClientAccountsRequest extends ListRequest {
  status?: AccountStatus[];
  subscriptionPlans?: string[];
  createdAfter?: string;
  createdBefore?: string;
  includeTrials?: boolean;
  includeInactive?: boolean;
}

export interface ListClientAccountsResponse extends ListResponse<ClientAccountSummary> {
  data: ClientAccountSummary[];
  statistics: AccountStatistics;
  subscriptionSummary: SubscriptionSummary;
  revenueSummary: RevenueSummary;
}

// Client Account Update APIs
export interface UpdateClientAccountRequest extends UpdateRequest<Partial<ClientAccountData>> {
  accountId: string;
  data: Partial<ClientAccountData>;
  updateType?: 'profile' | 'subscription' | 'billing' | 'settings' | 'status';
  notifyAdmin?: boolean;
}

export interface UpdateClientAccountResponse extends UpdateResponse<ClientAccount> {
  data: ClientAccount;
  changes: AccountChange[];
  subscriptionChanges: SubscriptionChange[];
  billingChanges: BillingChange[];
}

// Supporting Types for Client Account Management
export interface ClientAccountData {
  name: string;
  displayName?: string;
  description?: string;
  industry?: string;
  size?: CompanySize;
  website?: string;
  headquarters?: Address;
  contactInfo: ContactInfo;
  billingInfo?: BillingInformation;
  preferences?: AccountPreferences;
  settings?: AccountSettings;
}

export interface ClientAccount {
  id: string;
  name: string;
  displayName: string;
  status: AccountStatus;
  tier: AccountTier;
  subscription: SubscriptionInfo;
  users: number;
  engagements: number;
  createdAt: string;
  updatedAt: string;
  lastActivityAt?: string;
  metadata: Record<string, any>;
}

export interface AdminUserData {
  email: string;
  firstName: string;
  lastName: string;
  title?: string;
  phoneNumber?: string;
  timezone?: string;
  locale?: string;
}

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  displayName: string;
  status: string;
  roles: string[];
  createdAt: string;
}

export interface AccountUser {
  userId: string;
  email: string;
  displayName: string;
  roles: string[];
  status: string;
  lastLoginAt?: string;
  joinedAt: string;
}

export interface AccountEngagement {
  engagementId: string;
  name: string;
  type: string;
  status: string;
  startDate: string;
  endDate?: string;
  progress: number;
  teamSize: number;
}

export interface SubscriptionDetails {
  planId: string;
  planName: string;
  tier: AccountTier;
  status: SubscriptionStatus;
  startDate: string;
  endDate?: string;
  renewalDate?: string;
  features: SubscriptionFeature[];
  limits: SubscriptionLimits;
  billing: BillingCycle;
}

export interface BillingDetails {
  customerId: string;
  paymentMethod: PaymentMethod;
  billingAddress: Address;
  invoices: Invoice[];
  currentBalance: number;
  creditBalance: number;
  nextBillingDate?: string;
  billingHistory: BillingTransaction[];
}

export interface UsageMetrics {
  period: {
    start: string;
    end: string;
  };
  users: {
    active: number;
    total: number;
    limit: number;
  };
  engagements: {
    active: number;
    total: number;
    limit: number;
  };
  dataProcessed: {
    amount: number;
    unit: string;
    limit: number;
  };
  apiCalls: {
    count: number;
    limit: number;
  };
  storage: {
    used: number;
    limit: number;
    unit: string;
  };
}

export interface ClientAccountSummary {
  id: string;
  name: string;
  displayName: string;
  status: AccountStatus;
  tier: AccountTier;
  users: number;
  engagements: number;
  monthlyRevenue: number;
  lastActivityAt?: string;
  createdAt: string;
}

export interface AccountStatistics {
  total: number;
  active: number;
  trial: number;
  suspended: number;
  cancelled: number;
  byTier: Record<AccountTier, number>;
  byIndustry: Record<string, number>;
  growth: {
    newThisMonth: number;
    churnThisMonth: number;
    netGrowth: number;
  };
}

export interface SubscriptionSummary {
  totalSubscriptions: number;
  activeSubscriptions: number;
  trialSubscriptions: number;
  byPlan: Record<string, number>;
  totalMRR: number;
  averageRevenuePerUser: number;
  churnRate: number;
}

export interface RevenueSummary {
  totalRevenue: number;
  monthlyRecurringRevenue: number;
  annualRecurringRevenue: number;
  revenueGrowth: number;
  averageContractValue: number;
  customerLifetimeValue: number;
}

export interface AccountChange {
  field: string;
  oldValue: unknown;
  newValue: unknown;
  changedAt: string;
  changedBy: string;
  reason?: string;
}

export interface SubscriptionChange {
  type: 'plan_change' | 'feature_change' | 'limit_change' | 'billing_change';
  oldValue: unknown;
  newValue: unknown;
  effectiveDate: string;
  prorationAmount?: number;
}

export interface BillingChange {
  type: 'payment_method' | 'billing_address' | 'billing_cycle' | 'discount';
  oldValue: unknown;
  newValue: unknown;
  effectiveDate: string;
}

// Account Configuration Types
export interface AccountSetupConfig {
  features: string[];
  integrations: IntegrationConfig[];
  customizations: AccountCustomization[];
  onboardingSteps: OnboardingStep[];
}

export interface BillingInformation {
  companyName: string;
  taxId?: string;
  billingAddress: Address;
  paymentMethod: PaymentMethod;
  billingCycle: BillingCycle;
  currency: string;
  purchaseOrder?: string;
}

export interface AccountPreferences {
  timezone: string;
  dateFormat: string;
  currency: string;
  language: string;
  notifications: NotificationSettings;
  branding: BrandingSettings;
}

export interface AccountSettings {
  security: SecuritySettings;
  integrations: IntegrationSettings;
  dataRetention: DataRetentionSettings;
  compliance: ComplianceSettings;
  features: FeatureSettings;
}

// Supporting Enums and Types
export type AccountStatus = 'active' | 'trial' | 'suspended' | 'cancelled' | 'pending';
export type AccountTier = 'free' | 'basic' | 'professional' | 'enterprise' | 'custom';
export type CompanySize = 'startup' | 'small' | 'medium' | 'large' | 'enterprise';
export type SubscriptionStatus = 'active' | 'trial' | 'past_due' | 'cancelled' | 'paused';
export type BillingCycle = 'monthly' | 'quarterly' | 'annually' | 'custom';

export interface SubscriptionInfo {
  planId: string;
  planName: string;
  tier: AccountTier;
  status: SubscriptionStatus;
  startDate: string;
  endDate?: string;
}

export interface SubscriptionFeature {
  featureId: string;
  name: string;
  enabled: boolean;
  limit?: number;
  usage?: number;
}

export interface SubscriptionLimits {
  users: number;
  engagements: number;
  dataStorage: number;
  apiCalls: number;
  customRoles: number;
  integrations: number;
}

export interface PaymentMethod {
  type: 'credit_card' | 'bank_transfer' | 'invoice' | 'other';
  details: Record<string, any>;
  isDefault: boolean;
  expiresAt?: string;
}

export interface Invoice {
  invoiceId: string;
  number: string;
  amount: number;
  currency: string;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  issuedAt: string;
  dueAt: string;
  paidAt?: string;
  downloadUrl: string;
}

export interface BillingTransaction {
  transactionId: string;
  type: 'charge' | 'refund' | 'credit' | 'adjustment';
  amount: number;
  currency: string;
  description: string;
  status: 'pending' | 'completed' | 'failed';
  createdAt: string;
  completedAt?: string;
}

export interface Address {
  street: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
}

export interface ContactInfo {
  primaryEmail: string;
  phoneNumber?: string;
  website?: string;
  address?: Address;
}

export interface IntegrationConfig {
  type: string;
  enabled: boolean;
  configuration: Record<string, any>;
}

export interface AccountCustomization {
  type: string;
  configuration: Record<string, any>;
}

export interface OnboardingStep {
  stepId: string;
  name: string;
  completed: boolean;
  optional: boolean;
  order: number;
}

export interface NotificationSettings {
  email: boolean;
  inApp: boolean;
  sms: boolean;
  categories: Record<string, boolean>;
}

export interface BrandingSettings {
  logo?: string;
  primaryColor?: string;
  secondaryColor?: string;
  customCss?: string;
}

export interface SecuritySettings {
  twoFactorRequired: boolean;
  sessionTimeout: number;
  ipWhitelist?: string[];
  loginRestrictions: LoginRestriction[];
}

export interface IntegrationSettings {
  enabled: string[];
  configuration: Record<string, any>;
}

export interface DataRetentionSettings {
  logRetentionDays: number;
  dataExportEnabled: boolean;
  automaticCleanup: boolean;
}

export interface ComplianceSettings {
  frameworks: string[];
  dataProcessingAgreement: boolean;
  auditingEnabled: boolean;
}

export interface FeatureSettings {
  enabled: string[];
  configuration: Record<string, any>;
}

export interface LoginRestriction {
  type: 'time_based' | 'location_based' | 'device_based';
  configuration: Record<string, any>;
}