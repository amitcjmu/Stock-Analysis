/**
 * Account and Subscription Management Types
 * 
 * Account tiers, subscription management, billing information,
 * and payment processing types for admin account management.
 * 
 * Generated with CC for modular admin type organization.
 */

import type { Address } from './base-entities';

// Account and Subscription Related Types
export interface SubscriptionInfo {
  planId: string;
  planName: string;
  tier: AccountTier;
  status: SubscriptionStatus;
  startDate: string;
  endDate?: string;
  renewalDate?: string;
  autoRenew: boolean;
  features: SubscriptionFeature[];
  limits: SubscriptionLimits;
  usage: SubscriptionUsage;
  billing: BillingInfo;
}

export interface SubscriptionFeature {
  featureId: string;
  name: string;
  enabled: boolean;
  limit?: number;
  usage?: number;
  overageAllowed: boolean;
  overageRate?: number;
}

export interface SubscriptionLimits {
  users: LimitConfiguration;
  engagements: LimitConfiguration;
  dataStorage: LimitConfiguration;
  apiCalls: LimitConfiguration;
  integrations: LimitConfiguration;
  customRoles: LimitConfiguration;
  reports: LimitConfiguration;
  workspaces: LimitConfiguration;
}

export interface SubscriptionUsage {
  period: UsagePeriod;
  users: UsageMetric;
  engagements: UsageMetric;
  dataStorage: UsageMetric;
  apiCalls: UsageMetric;
  integrations: UsageMetric;
  reports: UsageMetric;
  lastUpdated: string;
}

export interface BillingInfo {
  customerId: string;
  paymentMethods: PaymentMethod[];
  defaultPaymentMethod?: string;
  billingAddress: Address;
  taxInfo: TaxInformation;
  invoices: Invoice[];
  credits: BillingCredit[];
  discounts: BillingDiscount[];
}

export interface PaymentMethod {
  id: string;
  type: PaymentMethodType;
  isDefault: boolean;
  details: PaymentMethodDetails;
  expiresAt?: string;
  status: PaymentMethodStatus;
  addedAt: string;
  lastUsed?: string;
}

export interface PaymentMethodDetails {
  // Credit Card Details
  lastFour?: string;
  brand?: string;
  expiryMonth?: number;
  expiryYear?: number;
  fingerprint?: string;
  
  // Bank Account Details
  bankName?: string;
  accountType?: string;
  routingNumber?: string;
  
  // Digital Wallet Details
  walletType?: string;
  walletEmail?: string;
  
  // Common Details
  billingAddress?: Address;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface TaxInformation {
  taxId?: string;
  vatNumber?: string;
  taxExempt: boolean;
  taxType: TaxType;
  jurisdiction: string;
  rates: TaxRate[];
}

export interface TaxRate {
  type: TaxType;
  rate: number;
  jurisdiction: string;
  effective_date: string;
  expiry_date?: string;
}

export interface Invoice {
  id: string;
  number: string;
  status: InvoiceStatus;
  amount: number;
  currency: string;
  issuedAt: string;
  dueAt: string;
  paidAt?: string;
  items: InvoiceItem[];
  taxes: InvoiceTax[];
  discounts: InvoiceDiscount[];
  payments: InvoicePayment[];
  downloadUrl?: string;
}

export interface InvoiceItem {
  id: string;
  description: string;
  quantity: number;
  unitPrice: number;
  total: number;
  taxable: boolean;
  periodStart?: string;
  periodEnd?: string;
}

export interface InvoiceTax {
  type: TaxType;
  rate: number;
  amount: number;
  jurisdiction: string;
}

export interface InvoiceDiscount {
  code?: string;
  description: string;
  amount: number;
  type: DiscountType;
}

export interface InvoicePayment {
  id: string;
  amount: number;
  method: PaymentMethodType;
  paidAt: string;
  reference?: string;
  status: PaymentStatus;
}

export interface BillingCredit {
  id: string;
  amount: number;
  currency: string;
  source: CreditSource;
  reason: string;
  appliedAt?: string;
  expiresAt?: string;
  metadata: Record<string, string | number | boolean | null>;
}

export interface BillingDiscount {
  id: string;
  code?: string;
  type: DiscountType;
  amount: number;
  percentage?: number;
  appliedAt: string;
  expiresAt?: string;
  restrictions?: DiscountRestriction[];
}

export interface DiscountRestriction {
  type: RestrictionType;
  value: unknown;
  message: string;
}

export interface LimitConfiguration {
  limit: number;
  soft_limit?: number;
  unit: string;
  period?: string;
  overageAllowed: boolean;
  overageRate?: number;
}

export interface UsageMetric {
  current: number;
  limit: number;
  unit: string;
  percentage: number;
  trend: TrendDirection;
  projectedExhaustion?: string;
}

export interface UsagePeriod {
  start: string;
  end: string;
  type: PeriodType;
  current: boolean;
}

// Account and subscription enums
export type AccountTier = 'free' | 'basic' | 'professional' | 'enterprise' | 'custom';
export type SubscriptionStatus = 'active' | 'trial' | 'past_due' | 'cancelled' | 'paused' | 'expired';
export type PaymentMethodType = 'credit_card' | 'debit_card' | 'bank_transfer' | 'paypal' | 'cryptocurrency';
export type PaymentMethodStatus = 'active' | 'expired' | 'suspended' | 'invalid';
export type TaxType = 'vat' | 'gst' | 'sales_tax' | 'withholding' | 'other';
export type InvoiceStatus = 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled' | 'refunded';
export type PaymentStatus = 'pending' | 'completed' | 'failed' | 'refunded' | 'disputed';
export type CreditSource = 'refund' | 'promotional' | 'error_correction' | 'goodwill' | 'migration';
export type DiscountType = 'percentage' | 'fixed_amount' | 'buy_x_get_y' | 'shipping' | 'trial_extension';
export type RestrictionType = 'user_tier' | 'usage_limit' | 'time_limit' | 'geographic' | 'feature_access';
export type TrendDirection = 'up' | 'down' | 'stable' | 'volatile';
export type PeriodType = 'monthly' | 'quarterly' | 'yearly' | 'billing_cycle';