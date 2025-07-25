/**
 * File Processing Types
 *
 * Common file processing interfaces used across file operations and import/export.
 */

export interface CompressionOptions {
  enabled: boolean;
  algorithm?: 'gzip' | 'brotli' | 'deflate';
  level?: number;
}

export interface EncryptionOptions {
  enabled: boolean;
  algorithm?: 'AES-256' | 'AES-128' | 'ChaCha20';
  keyDerivation?: 'PBKDF2' | 'scrypt' | 'bcrypt';
  password?: string;
  keyId?: string;
}

export interface ProcessingOptions {
  compression?: CompressionOptions;
  encryption?: EncryptionOptions;
  integrity?: {
    checksum: boolean;
    algorithm?: 'SHA-256' | 'SHA-512' | 'MD5';
  };
}
