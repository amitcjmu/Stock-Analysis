import React from 'react';
import { AlertTriangle, Shield, Clock, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface TechDebtSummaryCardsProps {
  summary: {
    totalItems: number;
    highRisk: number;
    criticalRisk: number;
    endOfLife: number;
    extendedSupport: number;
    deprecated: number;
  };
  onFilterChange: (filter: string, value: string) => void;
}

export const TechDebtSummaryCards: React.FC<TechDebtSummaryCardsProps> = ({
  summary,
  onFilterChange,
}) => {
  const cards = [
    {
      title: 'Critical Risks',
      value: summary.criticalRisk,
      icon: <AlertTriangle className="h-4 w-4 text-red-500" />,
      color: 'bg-red-50 text-red-600',
      filter: { type: 'risk', value: 'critical' },
    },
    {
      title: 'High Risks',
      value: summary.highRisk,
      icon: <Shield className="h-4 w-4 text-orange-500" />,
      color: 'bg-orange-50 text-orange-600',
      filter: { type: 'risk', value: 'high' },
    },
    {
      title: 'End of Life',
      value: summary.endOfLife,
      icon: <Clock className="h-4 w-4 text-purple-500" />,
      color: 'bg-purple-50 text-purple-600',
      filter: { type: 'status', value: 'end_of_life' },
    },
    {
      title: 'Extended Support',
      value: summary.extendedSupport,
      icon: <TrendingUp className="h-4 w-4 text-blue-500" />,
      color: 'bg-blue-50 text-blue-600',
      filter: { type: 'status', value: 'extended' },
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <Card 
          key={card.title}
          className="cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => onFilterChange(card.filter.type, card.filter.value)}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {card.title}
            </CardTitle>
            <div className={card.color + " p-2 rounded-full"}>
              {card.icon}
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{card.value}</div>
            <p className="text-xs text-muted-foreground">
              {card.title === 'Total Items' 
                ? 'across all components' 
                : `${Math.round((card.value / summary.totalItems) * 100)}% of total`}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};
