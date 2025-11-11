import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import {
  ExternalLink,
  GlobeIcon,
  BookOpenIcon,
  LinkIcon,
  DatabaseIcon,
  FolderIcon
} from 'lucide-react';
import type { Resource } from '../../types';

interface ResourceCardProps {
  resource: Resource;
}

export default function ResourceCard({ resource }: ResourceCardProps) {
  // Get icon based on resource type
  const getResourceIcon = () => {
    const iconClass = "h-6 w-6";
    switch (resource.resource_type) {
      case 'application':
        return <GlobeIcon className={iconClass} />;
      case 'wiki':
        return <BookOpenIcon className={iconClass} />;
      case 'link':
        return <LinkIcon className={iconClass} />;
      case 'dataset':
        return <DatabaseIcon className={iconClass} />;
      default:
        return <FolderIcon className={iconClass} />;
    }
  };

  // Open resource in new tab
  const handleOpen = () => {
    window.open(resource.url, '_blank', 'noopener,noreferrer');
  };

  // Get badge color based on resource type
  const getTypeBadgeVariant = () => {
    switch (resource.resource_type) {
      case 'application':
        return 'default';
      case 'link':
        return 'secondary';
      case 'wiki':
        return 'outline';
      default:
        return 'secondary';
    }
  };

  return (
    <Card className="shadow-md hover:shadow-lg transition-shadow cursor-pointer" onClick={handleOpen}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              {getResourceIcon()}
            </div>
            <div>
              <CardTitle className="text-lg">{resource.name}</CardTitle>
              <div className="flex gap-2 mt-1">
                <Badge variant={getTypeBadgeVariant()}>
                  {resource.resource_type}
                </Badge>
                {resource.course_specific && (
                  <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-300">
                    {resource.course_specific.toUpperCase()}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <CardDescription className="mb-4">
          {resource.description}
        </CardDescription>

        {/* Metadata Display */}
        {resource.metadata && Object.keys(resource.metadata).length > 0 && (
          <div className="mb-4 text-sm text-muted-foreground space-y-1">
            {resource.metadata.requires_auth && (
              <div className="flex items-center gap-2">
                <span className="font-medium">Authentication:</span>
                <span>Required</span>
              </div>
            )}
            {resource.metadata.documentation && (
              <div className="flex items-center gap-2">
                <span className="font-medium">Documentation:</span>
                <a
                  href={resource.metadata.documentation}
                  className="text-primary hover:underline"
                  onClick={(e) => e.stopPropagation()}
                >
                  View Docs
                </a>
              </div>
            )}
          </div>
        )}

        <Button className="w-full" onClick={handleOpen}>
          <ExternalLink className="h-4 w-4 mr-2" />
          Open Resource
        </Button>
      </CardContent>
    </Card>
  );
}
