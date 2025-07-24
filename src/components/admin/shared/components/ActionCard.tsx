/**
 * ActionCard Component
 * Reusable action/quick links card for admin dashboards
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { LucideIcon } from 'lucide-react';

export interface ActionItem {
  label: string;
  href: string;
  icon?: LucideIcon;
  variant?: 'default' | 'outline' | 'secondary' | 'destructive';
  badge?: {
    text: string | number;
    variant?: 'default' | 'secondary' | 'destructive' | 'outline';
  };
  disabled?: boolean;
}

export interface ActionCardProps {
  title: string;
  description?: string;
  actions: ActionItem[];
  className?: string;
}

export const ActionCard: React.FC<ActionCardProps> = ({
  title,
  description,
  actions,
  className = ''
}) => {
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent className="space-y-2">
        {actions.map((action) => {
          const ActionButton = (
            <Button
              asChild={!action.disabled}
              variant={action.variant || 'outline'}
              className="w-full justify-start"
              disabled={action.disabled}
            >
              {action.disabled ? (
                <div className="flex items-center">
                  {action.icon && <action.icon className="w-4 h-4 mr-2" />}
                  <span className="flex-1">{action.label}</span>
                  {action.badge && (
                    <Badge 
                      variant={action.badge.variant || 'secondary'} 
                      className="ml-2"
                    >
                      {action.badge.text}
                    </Badge>
                  )}
                </div>
              ) : (
                <Link to={action.href} className="flex items-center w-full">
                  {action.icon && <action.icon className="w-4 h-4 mr-2" />}
                  <span className="flex-1">{action.label}</span>
                  {action.badge && (
                    <Badge 
                      variant={action.badge.variant || 'secondary'} 
                      className="ml-2"
                    >
                      {action.badge.text}
                    </Badge>
                  )}
                </Link>
              )}
            </Button>
          );

          return (
            <div key={action.label}>
              {ActionButton}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
};