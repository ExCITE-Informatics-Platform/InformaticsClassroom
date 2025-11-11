import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import { Switch } from '../ui/switch';
import IconPicker from './IconPicker';
import type { Resource, ResourceFormData, ResourceType } from '../../types';

interface ResourceFormProps {
  resource?: Resource | null;
  onSubmit: (data: ResourceFormData) => void;
  onCancel: () => void;
  isSubmitting: boolean;
  courseSpecific?: string | null;
}

export default function ResourceForm({
  resource,
  onSubmit,
  onCancel,
  isSubmitting,
  courseSpecific = null,
}: ResourceFormProps) {
  const [formData, setFormData] = useState<ResourceFormData>({
    name: resource?.name || '',
    description: resource?.description || '',
    resource_type: resource?.resource_type || 'application',
    url: resource?.url || '',
    category: resource?.category || 'core_tools',
    order: resource?.order || 1,
    is_active: resource?.is_active ?? true,
    metadata: resource?.metadata || {},
  });

  const resourceTypes: ResourceType[] = [
    'application',
    'video',
    'document',
    'link',
    'wiki',
    'dataset',
    'other',
  ];

  const categories: string[] = [
    'core_tools',
    'tutorials',
    'documentation',
    'datasets',
    'projects',
    'supplemental',
    'other',
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleChange = (field: keyof ResourceFormData, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleMetadataChange = (key: string, value: any) => {
    setFormData((prev) => ({
      ...prev,
      metadata: {
        ...prev.metadata,
        [key]: value,
      },
    }));
  };

  // Get category display name
  const getCategoryName = (category: string): string => {
    const names: Record<string, string> = {
      'core_tools': 'Core Tools',
      'tutorials': 'Tutorials',
      'documentation': 'Documentation',
      'datasets': 'Datasets',
      'projects': 'Projects',
      'supplemental': 'Supplemental',
      'other': 'Other'
    };
    return names[category] || category;
  };

  // Render type-specific metadata fields
  const renderMetadataFields = () => {
    switch (formData.resource_type) {
      case 'video':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="duration">Duration (seconds)</Label>
              <Input
                id="duration"
                type="number"
                value={formData.metadata?.duration || ''}
                onChange={(e) => handleMetadataChange('duration', parseInt(e.target.value))}
                placeholder="Duration in seconds"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="author">Author</Label>
              <Input
                id="author"
                value={formData.metadata?.author || ''}
                onChange={(e) => handleMetadataChange('author', e.target.value)}
                placeholder="Video author/creator"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="published_date">Published Date</Label>
              <Input
                id="published_date"
                type="date"
                value={formData.metadata?.published_date || ''}
                onChange={(e) => handleMetadataChange('published_date', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="playlist">Playlist/Series</Label>
              <Input
                id="playlist"
                value={formData.metadata?.playlist || ''}
                onChange={(e) => handleMetadataChange('playlist', e.target.value)}
                placeholder="Part of a playlist or series"
              />
            </div>
          </>
        );

      case 'document':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="file_type">File Type</Label>
              <Input
                id="file_type"
                value={formData.metadata?.file_type || ''}
                onChange={(e) => handleMetadataChange('file_type', e.target.value)}
                placeholder="PDF, DOCX, PPTX, etc."
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="file_size">File Size (bytes)</Label>
              <Input
                id="file_size"
                type="number"
                value={formData.metadata?.file_size || ''}
                onChange={(e) => handleMetadataChange('file_size', parseInt(e.target.value))}
                placeholder="File size in bytes"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="pages">Number of Pages</Label>
              <Input
                id="pages"
                type="number"
                value={formData.metadata?.pages || ''}
                onChange={(e) => handleMetadataChange('pages', parseInt(e.target.value))}
                placeholder="Number of pages"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="doc_author">Author</Label>
              <Input
                id="doc_author"
                value={formData.metadata?.author || ''}
                onChange={(e) => handleMetadataChange('author', e.target.value)}
                placeholder="Document author"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="last_updated">Last Updated</Label>
              <Input
                id="last_updated"
                type="date"
                value={formData.metadata?.last_updated || ''}
                onChange={(e) => handleMetadataChange('last_updated', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="language">Language</Label>
              <Input
                id="language"
                value={formData.metadata?.language || ''}
                onChange={(e) => handleMetadataChange('language', e.target.value)}
                placeholder="English, Spanish, etc."
              />
            </div>
          </>
        );

      case 'application':
        return (
          <>
            <div className="flex items-center justify-between">
              <Label htmlFor="requires_auth">Requires Authentication</Label>
              <Switch
                id="requires_auth"
                checked={formData.metadata?.requires_auth || false}
                onCheckedChange={(checked) => handleMetadataChange('requires_auth', checked)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="documentation">Documentation URL</Label>
              <Input
                id="documentation"
                value={formData.metadata?.documentation || ''}
                onChange={(e) => handleMetadataChange('documentation', e.target.value)}
                placeholder="/docs/app or https://..."
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="version">Version</Label>
              <Input
                id="version"
                value={formData.metadata?.version || ''}
                onChange={(e) => handleMetadataChange('version', e.target.value)}
                placeholder="1.0.0"
              />
            </div>
          </>
        );

      case 'dataset':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="dataset_size">Dataset Size</Label>
              <Input
                id="dataset_size"
                value={formData.metadata?.dataset_size || ''}
                onChange={(e) => handleMetadataChange('dataset_size', e.target.value)}
                placeholder="10,000 rows, 5GB, etc."
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="format">Format</Label>
              <Input
                id="format"
                value={formData.metadata?.format || ''}
                onChange={(e) => handleMetadataChange('format', e.target.value)}
                placeholder="CSV, JSON, Parquet, etc."
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="license">License</Label>
              <Input
                id="license"
                value={formData.metadata?.license || ''}
                onChange={(e) => handleMetadataChange('license', e.target.value)}
                placeholder="MIT, Apache 2.0, CC-BY, etc."
              />
            </div>
          </>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={true} onOpenChange={onCancel}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {resource ? 'Edit Resource' : 'Create Resource'}
          </DialogTitle>
          <DialogDescription>
            {courseSpecific
              ? 'Add a course-specific resource for your students'
              : 'Add a general resource available to all users'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              required
              placeholder="Resource name"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description *</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              required
              placeholder="Brief description of the resource"
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="resource_type">Resource Type *</Label>
              <Select
                value={formData.resource_type}
                onValueChange={(value) => handleChange('resource_type', value as ResourceType)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {resourceTypes.map((type) => (
                    <SelectItem key={type} value={type} className="capitalize">
                      {type}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="category">Category *</Label>
              <Select
                value={formData.category}
                onValueChange={(value) => handleChange('category', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((category) => (
                    <SelectItem key={category} value={category}>
                      {getCategoryName(category)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="url">URL *</Label>
            <Input
              id="url"
              type="url"
              value={formData.url}
              onChange={(e) => handleChange('url', e.target.value)}
              required
              placeholder="https://..."
            />
          </div>

          {/* Icon Picker */}
          <IconPicker
            value={
              formData.metadata?.icon_type && formData.metadata?.icon_value
                ? { type: formData.metadata.icon_type, value: formData.metadata.icon_value }
                : undefined
            }
            onChange={(icon) => {
              handleMetadataChange('icon_type', icon.type);
              handleMetadataChange('icon_value', icon.value);
            }}
          />

          <div className="space-y-2">
            <Label htmlFor="order">Display Order</Label>
            <Input
              id="order"
              type="number"
              value={formData.order}
              onChange={(e) => handleChange('order', parseInt(e.target.value))}
              min={1}
            />
          </div>

          <div className="flex items-center justify-between">
            <Label htmlFor="is_active">Active</Label>
            <Switch
              id="is_active"
              checked={formData.is_active}
              onCheckedChange={(checked) => handleChange('is_active', checked)}
            />
          </div>

          {/* Type-specific metadata fields */}
          {renderMetadataFields()}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : resource ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
