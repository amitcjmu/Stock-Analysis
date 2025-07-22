/**
 * Base Entity Types and Core Interfaces
 * 
 * Foundational entity types and base interfaces used across
 * all admin data models. Provides common structure and audit capabilities.
 * 
 * Generated with CC for modular admin type organization.
 */

// Core Entity Types that are referenced across multiple modules
export interface BaseEntity {
  id: string;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  updatedBy?: string;
  version: number;
  metadata: Record<string, any>;
}

export interface AuditableEntity extends BaseEntity {
  auditTrail: AuditTrailEntry[];
  lastAuditedAt?: string;
  complianceStatus: ComplianceStatus;
}

export interface SoftDeletableEntity extends BaseEntity {
  deletedAt?: string;
  deletedBy?: string;
  deletionReason?: string;
  isDeleted: boolean;
}

// Shared Supporting Data Types
export interface Address {
  street: string;
  street2?: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
  formatted?: string;
  coordinates?: GeographicCoordinates;
}

export interface ContactInfo {
  primaryEmail: string;
  secondaryEmail?: string;
  primaryPhone?: string;
  secondaryPhone?: string;
  website?: string;
  socialMedia?: SocialMediaContact[];
  preferredContactMethod?: ContactMethod;
  address?: Address;
}

export interface GeographicCoordinates {
  latitude: number;
  longitude: number;
  accuracy?: number;
  source?: CoordinateSource;
}

export interface SocialMediaContact {
  platform: SocialMediaPlatform;
  handle: string;
  url: string;
  verified: boolean;
}

export interface PersonalInfo {
  firstName: string;
  lastName: string;
  middleName?: string;
  displayName?: string;
  preferredName?: string;
  title?: string;
  suffix?: string;
  dateOfBirth?: string;
  profileImage?: string;
  bio?: string;
  pronouns?: string;
}

export interface ProfessionalInfo {
  title?: string;
  department?: string;
  division?: string;
  manager?: string;
  reports?: string[];
  startDate?: string;
  endDate?: string;
  employeeId?: string;
  location?: string;
  workLocation?: WorkLocationType;
  skills?: Skill[];
  certifications?: Certification[];
  experience?: WorkExperience[];
}

// Core audit and compliance types
export interface AuditTrailEntry {
  id: string;
  timestamp: string;
  userId?: string;
  action: string;
  resource: string;
  resourceId?: string;
  changes: FieldChange[];
  metadata: Record<string, any>;
  ipAddress?: string;
  userAgent?: string;
  sessionId?: string;
}

export interface FieldChange {
  field: string;
  oldValue: unknown;
  newValue: unknown;
  changeType: ChangeType;
  sensitive: boolean;
  encrypted: boolean;
}

// Skills and certifications
export interface Skill {
  name: string;
  category: SkillCategory;
  level: SkillLevel;
  verified: boolean;
  endorsements: SkillEndorsement[];
  certifications: string[];
  lastUsed?: string;
}

export interface Certification {
  name: string;
  issuer: string;
  issuedDate: string;
  expiryDate?: string;
  credentialId?: string;
  verificationUrl?: string;
  status: CertificationStatus;
}

export interface WorkExperience {
  company: string;
  title: string;
  startDate: string;
  endDate?: string;
  current: boolean;
  description?: string;
  skills: string[];
  achievements: string[];
}

export interface SkillEndorsement {
  endorserId: string;
  endorserName: string;
  endorsedAt: string;
  relationship: EndorsementRelationship;
  verified: boolean;
}

// Core enums used by base entities
export type ComplianceStatus = 'compliant' | 'non_compliant' | 'pending' | 'not_applicable';
export type ContactMethod = 'email' | 'phone' | 'sms' | 'chat' | 'video' | 'in_person';
export type CoordinateSource = 'gps' | 'ip_lookup' | 'manual' | 'geocoded';
export type SocialMediaPlatform = 'linkedin' | 'twitter' | 'facebook' | 'instagram' | 'github' | 'youtube';
export type WorkLocationType = 'office' | 'remote' | 'hybrid' | 'field' | 'client_site';
export type ChangeType = 'create' | 'update' | 'delete' | 'restore' | 'archive' | 'merge';
export type SkillCategory = 'technical' | 'business' | 'creative' | 'communication' | 'leadership' | 'analytical';
export type SkillLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert' | 'master';
export type CertificationStatus = 'active' | 'expired' | 'suspended' | 'revoked' | 'pending';
export type EndorsementRelationship = 'colleague' | 'manager' | 'client' | 'subordinate' | 'peer' | 'other';