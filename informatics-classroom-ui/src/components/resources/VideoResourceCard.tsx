import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { VideoIcon, PlayCircle, ExternalLink, Clock } from 'lucide-react';
import type { Resource } from '../../types';

interface VideoResourceCardProps {
  resource: Resource;
}

export default function VideoResourceCard({ resource }: VideoResourceCardProps) {
  // Extract YouTube video ID if it's a YouTube link
  const getYouTubeId = (url: string): string | null => {
    const patterns = [
      /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/,
      /youtube\.com\/shorts\/([^&\n?#]+)/
    ];

    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match && match[1]) {
        return match[1];
      }
    }
    return null;
  };

  const youtubeId = getYouTubeId(resource.url);
  const thumbnailUrl = youtubeId
    ? `https://img.youtube.com/vi/${youtubeId}/hqdefault.jpg`
    : null;

  // Open video in new tab
  const handleOpen = () => {
    window.open(resource.url, '_blank', 'noopener,noreferrer');
  };

  // Format duration from metadata
  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return secs > 0 ? `${minutes}m ${secs}s` : `${minutes}m`;
  };

  return (
    <Card className="shadow-md hover:shadow-lg transition-shadow overflow-hidden">
      {/* Thumbnail Section */}
      <div className="relative aspect-video bg-muted">
        {thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt={resource.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <VideoIcon className="h-12 w-12 text-muted-foreground" />
          </div>
        )}
        <div className="absolute inset-0 bg-black/30 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity cursor-pointer" onClick={handleOpen}>
          <PlayCircle className="h-16 w-16 text-white" />
        </div>
        {resource.metadata?.duration && (
          <div className="absolute bottom-2 right-2 bg-black/80 text-white px-2 py-1 rounded text-xs flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {formatDuration(resource.metadata.duration)}
          </div>
        )}
      </div>

      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{resource.name}</CardTitle>
            <div className="flex gap-2 mt-1">
              <Badge variant="default">
                <VideoIcon className="h-3 w-3 mr-1" />
                Video
              </Badge>
              {resource.course_specific && (
                <Badge variant="outline">Course-Specific</Badge>
              )}
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <CardDescription className="mb-4">
          {resource.description}
        </CardDescription>

        {/* Video Metadata */}
        {resource.metadata && (
          <div className="mb-4 text-sm text-muted-foreground space-y-1">
            {resource.metadata.author && (
              <div className="flex items-center gap-2">
                <span className="font-medium">Author:</span>
                <span>{resource.metadata.author}</span>
              </div>
            )}
            {resource.metadata.published_date && (
              <div className="flex items-center gap-2">
                <span className="font-medium">Published:</span>
                <span>{new Date(resource.metadata.published_date).toLocaleDateString()}</span>
              </div>
            )}
            {resource.metadata.playlist && (
              <div className="flex items-center gap-2">
                <span className="font-medium">Part of:</span>
                <span>{resource.metadata.playlist}</span>
              </div>
            )}
          </div>
        )}

        <Button className="w-full" onClick={handleOpen}>
          <PlayCircle className="h-4 w-4 mr-2" />
          Watch Video
        </Button>
      </CardContent>
    </Card>
  );
}
