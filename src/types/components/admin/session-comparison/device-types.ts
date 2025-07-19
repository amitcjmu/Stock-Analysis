/**
 * Device and Browser Types
 * 
 * Device, browser, and network information types for session comparison.
 */

import { DeviceType, ConnectionType, ProxyType } from './enum-types';

export interface DeviceInfo {
  type: DeviceType;
  os: OperatingSystem;
  brand?: string;
  model?: string;
  fingerprint: string;
  trusted: boolean;
  registeredAt?: string;
  lastSeen: string;
}

export interface OperatingSystem {
  name: string;
  version: string;
  platform: string;
  architecture?: string;
}

export interface LocationInfo {
  ip: string;
  country?: string;
  region?: string;
  city?: string;
  timezone?: string;
  coordinates?: [number, number];
  isp?: string;
  organization?: string;
  asn?: string;
  vpn: boolean;
  proxy: boolean;
  tor: boolean;
}

export interface NetworkInfo {
  connectionType: ConnectionType;
  bandwidth?: number;
  latency?: number;
  protocol: string;
  encryption: EncryptionInfo;
  proxy?: ProxyInfo;
  cdn?: CdnInfo;
  requestsCount: number;
  bytesTransferred: number;
  bytesReceived: number;
}

export interface EncryptionInfo {
  protocol: string;
  cipher: string;
  keySize: number;
  version: string;
  certificateValid: boolean;
}

export interface ProxyInfo {
  type: ProxyType;
  address: string;
  port: number;
  authentication: boolean;
  trusted: boolean;
}

export interface CdnInfo {
  provider: string;
  edge: string;
  cacheHit: boolean;
  responseTime: number;
}

export interface BrowserInfo {
  name: string;
  version: string;
  engine: string;
  userAgent: string;
  language: string;
  languages: string[];
  cookiesEnabled: boolean;
  javaScriptEnabled: boolean;
  adBlocker: boolean;
  plugins: BrowserPlugin[];
  extensions: BrowserExtension[];
  viewport: Viewport;
  screen: ScreenInfo;
}

export interface BrowserPlugin {
  name: string;
  version: string;
  enabled: boolean;
  filename?: string;
}

export interface BrowserExtension {
  id: string;
  name: string;
  version: string;
  enabled: boolean;
  permissions: string[];
}

export interface Viewport {
  width: number;
  height: number;
  devicePixelRatio: number;
  orientation: 'portrait' | 'landscape';
}

export interface ScreenInfo {
  width: number;
  height: number;
  colorDepth: number;
  pixelDepth: number;
  availWidth: number;
  availHeight: number;
}