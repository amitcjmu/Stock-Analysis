/**
 * Version utility to extract current version from changelog
 */

// Extract version from changelog - this will be the first version entry
export const getCurrentVersion = (): string => {
  // Since we can't dynamically read the changelog file in the browser,
  // we'll manually update this when the version changes
  // This should match the latest version in CHANGELOG.md
  return '0.4.9';
};

export const getVersionInfo = () => {
  const version = getCurrentVersion();
  return {
    version,
    fullVersion: `AI Modernize v${version}`,
    buildDate: new Date().toLocaleDateString(),
  };
}; 