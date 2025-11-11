import { useState } from 'react';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Button } from '../ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Badge } from '../ui/badge';
import {
  GlobeIcon,
  BookOpenIcon,
  VideoIcon,
  FileTextIcon,
  LinkIcon,
  DatabaseIcon,
  FolderIcon,
  Code2Icon,
  Server,
  Cloud,
  Cpu,
  HardDrive,
  Network,
  Terminal,
  Box,
  Package,
  Layers,
  GitBranch,
  Github,
  FileCode,
  FileJson,
  FileCog,
  BookMarked,
  GraduationCap,
  Library,
  Microscope,
  FlaskConical,
  Activity,
  BarChart,
  LineChart,
  PieChart,
  TrendingUp,
  Calculator,
  Beaker,
  Search,
} from 'lucide-react';

interface IconPickerProps {
  value?: {
    type: 'lucide' | 'url' | 'emoji';
    value: string;
  };
  onChange: (icon: { type: 'lucide' | 'url' | 'emoji'; value: string }) => void;
}

// Popular Lucide icons for resources
const LUCIDE_ICONS = [
  { name: 'GlobeIcon', icon: GlobeIcon, label: 'Globe' },
  { name: 'BookOpenIcon', icon: BookOpenIcon, label: 'Book' },
  { name: 'VideoIcon', icon: VideoIcon, label: 'Video' },
  { name: 'FileTextIcon', icon: FileTextIcon, label: 'Document' },
  { name: 'LinkIcon', icon: LinkIcon, label: 'Link' },
  { name: 'DatabaseIcon', icon: DatabaseIcon, label: 'Database' },
  { name: 'FolderIcon', icon: FolderIcon, label: 'Folder' },
  { name: 'Code2Icon', icon: Code2Icon, label: 'Code' },
  { name: 'Server', icon: Server, label: 'Server' },
  { name: 'Cloud', icon: Cloud, label: 'Cloud' },
  { name: 'Cpu', icon: Cpu, label: 'CPU' },
  { name: 'HardDrive', icon: HardDrive, label: 'Storage' },
  { name: 'Network', icon: Network, label: 'Network' },
  { name: 'Terminal', icon: Terminal, label: 'Terminal' },
  { name: 'Box', icon: Box, label: 'Box' },
  { name: 'Package', icon: Package, label: 'Package' },
  { name: 'Layers', icon: Layers, label: 'Layers' },
  { name: 'GitBranch', icon: GitBranch, label: 'Git' },
  { name: 'Github', icon: Github, label: 'GitHub' },
  { name: 'FileCode', icon: FileCode, label: 'Code File' },
  { name: 'FileJson', icon: FileJson, label: 'JSON' },
  { name: 'FileCog', icon: FileCog, label: 'Config' },
  { name: 'BookMarked', icon: BookMarked, label: 'Tutorial' },
  { name: 'GraduationCap', icon: GraduationCap, label: 'Education' },
  { name: 'Library', icon: Library, label: 'Library' },
  { name: 'Microscope', icon: Microscope, label: 'Research' },
  { name: 'FlaskConical', icon: FlaskConical, label: 'Lab' },
  { name: 'Activity', icon: Activity, label: 'Activity' },
  { name: 'BarChart', icon: BarChart, label: 'Bar Chart' },
  { name: 'LineChart', icon: LineChart, label: 'Line Chart' },
  { name: 'PieChart', icon: PieChart, label: 'Pie Chart' },
  { name: 'TrendingUp', icon: TrendingUp, label: 'Analytics' },
  { name: 'Calculator', icon: Calculator, label: 'Calculator' },
  { name: 'Beaker', icon: Beaker, label: 'Experiment' },
];

export default function IconPicker({ value, onChange }: IconPickerProps) {
  const [activeTab, setActiveTab] = useState('lucide');
  const [searchQuery, setSearchQuery] = useState('');
  const [customUrl, setCustomUrl] = useState(value?.type === 'url' ? value.value : '');
  const [emoji, setEmoji] = useState(value?.type === 'emoji' ? value.value : '');

  // Filter icons based on search
  const filteredIcons = LUCIDE_ICONS.filter((icon) =>
    icon.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
    icon.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleLucideSelect = (iconName: string) => {
    onChange({ type: 'lucide', value: iconName });
  };

  const handleUrlSubmit = () => {
    if (customUrl.trim()) {
      onChange({ type: 'url', value: customUrl.trim() });
    }
  };

  const handleEmojiSubmit = () => {
    if (emoji.trim()) {
      onChange({ type: 'emoji', value: emoji.trim() });
    }
  };

  // Render preview of current selection
  const renderPreview = () => {
    if (!value) return null;

    if (value.type === 'lucide') {
      const iconData = LUCIDE_ICONS.find(i => i.name === value.value);
      if (iconData) {
        const Icon = iconData.icon;
        return (
          <div className="flex items-center gap-2 p-3 bg-primary/10 rounded-lg">
            <Icon className="h-8 w-8 text-primary" />
            <div>
              <p className="text-sm font-medium">Selected: {iconData.label}</p>
              <p className="text-xs text-muted-foreground">Lucide Icon</p>
            </div>
          </div>
        );
      }
    } else if (value.type === 'url') {
      return (
        <div className="flex items-center gap-2 p-3 bg-primary/10 rounded-lg">
          <img src={value.value} alt="Custom icon" className="h-8 w-8 object-contain" />
          <div>
            <p className="text-sm font-medium">Custom Image</p>
            <p className="text-xs text-muted-foreground truncate max-w-[200px]">{value.value}</p>
          </div>
        </div>
      );
    } else if (value.type === 'emoji') {
      return (
        <div className="flex items-center gap-2 p-3 bg-primary/10 rounded-lg">
          <span className="text-3xl">{value.value}</span>
          <div>
            <p className="text-sm font-medium">Emoji Icon</p>
            <p className="text-xs text-muted-foreground">Unicode Character</p>
          </div>
        </div>
      );
    }
  };

  return (
    <div className="space-y-4">
      <Label>Resource Icon</Label>

      {/* Current Selection Preview */}
      {renderPreview()}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="lucide">Icon Library</TabsTrigger>
          <TabsTrigger value="url">Image URL</TabsTrigger>
          <TabsTrigger value="emoji">Emoji</TabsTrigger>
        </TabsList>

        {/* Lucide Icons Tab */}
        <TabsContent value="lucide" className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search icons..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          <div className="grid grid-cols-6 gap-2 max-h-64 overflow-y-auto p-2 border rounded-lg">
            {filteredIcons.map((iconData) => {
              const Icon = iconData.icon;
              const isSelected = value?.type === 'lucide' && value.value === iconData.name;

              return (
                <button
                  key={iconData.name}
                  type="button"
                  onClick={() => handleLucideSelect(iconData.name)}
                  className={`p-3 rounded-lg hover:bg-primary/10 transition-colors flex flex-col items-center gap-1 ${
                    isSelected ? 'bg-primary/20 ring-2 ring-primary' : ''
                  }`}
                  title={iconData.label}
                >
                  <Icon className="h-6 w-6" />
                  <span className="text-[10px] text-center line-clamp-1">{iconData.label}</span>
                </button>
              );
            })}
          </div>

          {filteredIcons.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-4">No icons found</p>
          )}
        </TabsContent>

        {/* Custom URL Tab */}
        <TabsContent value="url" className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="icon-url">Image URL</Label>
            <Input
              id="icon-url"
              type="url"
              placeholder="https://example.com/icon.png"
              value={customUrl}
              onChange={(e) => setCustomUrl(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Enter a URL to an image file (PNG, SVG, JPG recommended)
            </p>
          </div>

          {customUrl && (
            <div className="border rounded-lg p-4">
              <p className="text-sm font-medium mb-2">Preview:</p>
              <img
                src={customUrl}
                alt="Icon preview"
                className="h-16 w-16 object-contain"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
            </div>
          )}

          <Button
            type="button"
            onClick={handleUrlSubmit}
            disabled={!customUrl.trim()}
            className="w-full"
          >
            Use This Image
          </Button>
        </TabsContent>

        {/* Emoji Tab */}
        <TabsContent value="emoji" className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="emoji-icon">Emoji Character</Label>
            <Input
              id="emoji-icon"
              placeholder="📚 🎓 💻 🔬"
              value={emoji}
              onChange={(e) => setEmoji(e.target.value)}
              maxLength={2}
            />
            <p className="text-xs text-muted-foreground">
              Enter an emoji character (copy/paste or use emoji keyboard)
            </p>
          </div>

          {/* Common emoji suggestions */}
          <div className="space-y-2">
            <Label className="text-xs">Popular Choices:</Label>
            <div className="grid grid-cols-8 gap-2">
              {['📚', '🎓', '💻', '🔬', '📊', '🧪', '🗂️', '📝', '🎥', '🔗', '🌐', '⚙️', '🖥️', '📱', '☁️', '🔐'].map((e) => (
                <button
                  key={e}
                  type="button"
                  onClick={() => setEmoji(e)}
                  className="text-2xl p-2 hover:bg-primary/10 rounded-lg transition-colors"
                >
                  {e}
                </button>
              ))}
            </div>
          </div>

          {emoji && (
            <div className="border rounded-lg p-4 text-center">
              <p className="text-sm font-medium mb-2">Preview:</p>
              <span className="text-5xl">{emoji}</span>
            </div>
          )}

          <Button
            type="button"
            onClick={handleEmojiSubmit}
            disabled={!emoji.trim()}
            className="w-full"
          >
            Use This Emoji
          </Button>
        </TabsContent>
      </Tabs>
    </div>
  );
}
