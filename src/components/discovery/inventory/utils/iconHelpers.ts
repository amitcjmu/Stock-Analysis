import { Server, Database, Cpu, Router, Shield } from 'lucide-react';

export const getTypeIcon = (type: string) => {
  const typeStr = type?.toLowerCase() || '';
  if (typeStr.includes('server')) return Server;
  if (typeStr.includes('database')) return Database;
  if (typeStr.includes('application')) return Cpu;
  if (typeStr.includes('network') || typeStr.includes('device')) return Router;
  return Shield;
};

export const getReadinessColor = (readiness: number | undefined) => {
  if (!readiness) return 'gray';
  if (readiness >= 80) return 'green';
  if (readiness >= 60) return 'yellow';
  return 'red';
};