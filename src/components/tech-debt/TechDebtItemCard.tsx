import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { Info } from 'lucide-react'
import { AlertTriangle, CheckCircle, ExternalLink } from 'lucide-react'
import { TechDebtItem } from '@/types/tech-debt';

interface TechDebtItemCardProps {
  item: TechDebtItem;
  isSelected: boolean;
  onSelect: (id: string, selected: boolean) => void;
  onViewDetails: (item: TechDebtItem) => void;
  showCheckbox?: boolean;
}

export function TechDebtItemCard({ 
  item, 
  isSelected, 
  onSelect, 
  onViewDetails, 
  showCheckbox = true 
}: TechDebtItemCardProps) {
  const getRiskBadgeVariant = () => {
    switch (item.securityRisk) {
      case 'critical':
        return 'destructive';
      case 'high':
        return 'destructive'; // Changed from 'warning' to 'destructive' to match variant type
      case 'medium':
        return 'secondary';
      case 'low':
      default:
        return 'outline';
    }
  };

  const getStatusBadgeVariant = () => {
    switch (item.status) {
      case 'active':
        return 'destructive';
      case 'mitigated':
        return 'outline'; // Changed from 'success' to 'outline' to match variant type
      case 'planned':
        return 'secondary'; // Changed from 'warning' to 'secondary' to match variant type
      default:
        return 'outline';
    }
  };

  return (
    <Card className={`overflow-hidden transition-colors ${isSelected ? 'ring-2 ring-primary' : ''}`}>
      <CardHeader className="flex flex-row items-start justify-between space-y-0 p-4 pb-2">
        <div className="flex items-center space-x-2">
          {showCheckbox && (
            <Checkbox
              id={`select-${item.id}`}
              checked={isSelected}
              onCheckedChange={(checked) => onSelect(item.id, checked as boolean)}
              className="h-5 w-5 rounded-md mr-2"
            />
          )}
          <div>
            <CardTitle className="text-lg font-semibold">{item.name}</CardTitle>
            <CardDescription className="text-sm text-muted-foreground">
              {item.resourceType} • {item.resourceId}
            </CardDescription>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant={getRiskBadgeVariant()} className="capitalize">
            {item.securityRisk} risk
          </Badge>
          <Badge variant={getStatusBadgeVariant()} className="capitalize">
            {item.status}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="p-4 pt-0">
        <p className="mb-3 line-clamp-2 text-sm text-muted-foreground">
          {item.description}
        </p>
        
        <div className="mt-2 flex flex-wrap gap-2">
          {item.tags?.map((tag) => (
            <Badge key={tag} variant="outline" className="text-xs">
              {tag}
            </Badge>
          ))}
        </div>

        {item.supportStatus === 'end_of_life' && (
          <div className="mt-3 flex items-center rounded-md bg-amber-50 p-2 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400">
            <AlertTriangle className="mr-2 h-4 w-4 flex-shrink-0" />
            <span className="text-xs">End of life: {item.supportStatus}</span>
          </div>
        )}

        {item.recommendations?.length > 0 && (
          <div className="mt-3">
            <h4 className="mb-1 text-sm font-medium">Recommendations</h4>
            <ul className="space-y-1 text-sm text-muted-foreground">
              {item.recommendations.slice(0, 2).map((rec, i) => (
                <li key={i} className="flex items-start">
                  <CheckCircle className="mr-2 mt-0.5 h-4 w-4 flex-shrink-0 text-green-500" />
                  <span>{rec}</span>
                </li>
              ))}
              {item.recommendations.length > 2 && (
                <li className="text-xs text-muted-foreground/70">
                  +{item.recommendations.length - 2} more recommendations
                </li>
              )}
            </ul>
          </div>
        )}
      </CardContent>
      
      <CardFooter className="flex items-center justify-between border-t bg-muted/20 p-4">
        <div className="flex items-center space-x-2 text-xs text-muted-foreground">
          <span>Last scanned: {new Date(item.lastScanned).toLocaleDateString()}</span>
          <Tooltip>
            <TooltipTrigger asChild>
              <button type="button" className="text-muted-foreground/70 hover:text-foreground">
                <Info className="h-3.5 w-3.5" />
              </button>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-[300px] text-xs">
              <p>Impact: {item.impact}/5 • Effort: {item.effort}/5 • Priority: {item.priority}/5</p>
            </TooltipContent>
          </Tooltip>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onViewDetails(item)}
          className="h-8"
        >
          <ExternalLink className="mr-1 h-3.5 w-3.5" />
          Details
        </Button>
      </CardFooter>
    </Card>
  );
}
