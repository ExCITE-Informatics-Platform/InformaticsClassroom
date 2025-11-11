import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import {
  FileTextIcon,
  Download,
  ExternalLink,
  FileIcon,
  Presentation,
  Sheet
} from 'lucide-react';
import type { Resource } from '../../types';

interface DocumentResourceCardProps {
  resource: Resource;
}

export default function DocumentResourceCard({ resource }: DocumentResourceCardProps) {
  // Get document icon based on file type
  const getDocumentIcon = () => {
    const iconClass = "h-6 w-6";
    const fileType = resource.metadata?.file_type?.toLowerCase() || '';

    if (fileType.includes('pdf')) {
      return <FileTextIcon className={iconClass} />;
    } else if (fileType.includes('presentation') || fileType.includes('ppt') || fileType.includes('slides')) {
      return <Presentation className={iconClass} />;
    } else if (fileType.includes('spreadsheet') || fileType.includes('xls') || fileType.includes('csv')) {
      return <Sheet className={iconClass} />;
    }
    return <FileIcon className={iconClass} />;
  };

  // Get file extension from URL or metadata
  const getFileExtension = (): string => {
    const fileType = resource.metadata?.file_type;
    if (fileType) return fileType.toUpperCase();

    const urlParts = resource.url.split('.');
    if (urlParts.length > 1) {
      return urlParts[urlParts.length - 1].toUpperCase();
    }
    return 'DOC';
  };

  // Format file size from bytes
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  // Open document in new tab
  const handleOpen = () => {
    window.open(resource.url, '_blank', 'noopener,noreferrer');
  };

  // Download document
  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
    const link = document.createElement('a');
    link.href = resource.url;
    link.download = resource.metadata?.filename || resource.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <Card className="shadow-md hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              {getDocumentIcon()}
            </div>
            <div>
              <CardTitle className="text-lg">{resource.name}</CardTitle>
              <div className="flex gap-2 mt-1">
                <Badge variant="default">
                  <FileTextIcon className="h-3 w-3 mr-1" />
                  {getFileExtension()}
                </Badge>
                {resource.course_specific && (
                  <Badge variant="outline">Course-Specific</Badge>
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

        {/* Document Metadata */}
        {resource.metadata && (
          <div className="mb-4 text-sm text-muted-foreground space-y-1">
            {resource.metadata.file_size && (
              <div className="flex items-center gap-2">
                <span className="font-medium">Size:</span>
                <span>{formatFileSize(resource.metadata.file_size)}</span>
              </div>
            )}
            {resource.metadata.pages && (
              <div className="flex items-center gap-2">
                <span className="font-medium">Pages:</span>
                <span>{resource.metadata.pages}</span>
              </div>
            )}
            {resource.metadata.author && (
              <div className="flex items-center gap-2">
                <span className="font-medium">Author:</span>
                <span>{resource.metadata.author}</span>
              </div>
            )}
            {resource.metadata.last_updated && (
              <div className="flex items-center gap-2">
                <span className="font-medium">Updated:</span>
                <span>{new Date(resource.metadata.last_updated).toLocaleDateString()}</span>
              </div>
            )}
            {resource.metadata.language && (
              <div className="flex items-center gap-2">
                <span className="font-medium">Language:</span>
                <span>{resource.metadata.language}</span>
              </div>
            )}
          </div>
        )}

        <div className="grid grid-cols-2 gap-2">
          <Button variant="outline" onClick={handleOpen}>
            <ExternalLink className="h-4 w-4 mr-2" />
            Open
          </Button>
          <Button onClick={handleDownload}>
            <Download className="h-4 w-4 mr-2" />
            Download
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
