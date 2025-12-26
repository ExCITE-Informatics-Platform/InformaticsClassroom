import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { classesService, type ClassMember, type ClassMembersResponse, type ImportStudentsResponse } from '../../services/classes';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import { Plus, Trash2, AlertCircle, Loader2, Users, Upload, FileText, CheckCircle2 } from 'lucide-react';

interface StudentsTabProps {
  classId: string;
}

interface AddMemberFormData {
  user_id: string;
  email: string;
  role: 'instructor' | 'ta' | 'student';
}

export default function StudentsTab({ classId }: StudentsTabProps) {
  const queryClient = useQueryClient();
  const [showAddForm, setShowAddForm] = useState(false);
  const [addMemberForm, setAddMemberForm] = useState<AddMemberFormData>({
    user_id: '',
    email: '',
    role: 'student',
  });
  const [editingMember, setEditingMember] = useState<string | null>(null);
  const [editRole, setEditRole] = useState<'instructor' | 'ta' | 'student'>('student');
  const [showImportForm, setShowImportForm] = useState(false);
  const [importText, setImportText] = useState('');
  const [importResults, setImportResults] = useState<ImportStudentsResponse | null>(null);

  // Fetch class members
  const {
    data: membersData,
    isLoading: loadingMembers,
    error: membersError,
  } = useQuery<ClassMembersResponse | null>({
    queryKey: ['class', 'members', classId],
    queryFn: async (): Promise<ClassMembersResponse | null> => {
      if (!classId) return null;
      const response = await classesService.getClassMembers(classId);
      if (!response.success) {
        throw new Error(response.error || 'Failed to load members');
      }
      // Unwrap ApiResponse if needed
      if ('data' in response && response.data) {
        return response.data as ClassMembersResponse;
      }
      return response as ClassMembersResponse;
    },
    enabled: !!classId,
  });

  // Add member mutation
  const addMemberMutation = useMutation({
    mutationFn: async (data: AddMemberFormData) => {
      if (!classId) throw new Error('No class selected');
      const response = await classesService.addClassMember(classId, {
        user_id: data.user_id || data.email,
        role: data.role,
      });
      if (!response.success) {
        throw new Error(response.error || 'Failed to add member');
      }
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['class', 'members', classId] });
      setShowAddForm(false);
      setAddMemberForm({ user_id: '', email: '', role: 'student' });
    },
  });

  // Update member mutation
  const updateMemberMutation = useMutation({
    mutationFn: async ({ userId, role }: { userId: string; role: 'instructor' | 'ta' | 'student' }) => {
      if (!classId) throw new Error('No class selected');
      const response = await classesService.updateClassMember(classId, userId, { role });
      if (!response.success) {
        throw new Error(response.error || 'Failed to update member');
      }
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['class', 'members', classId] });
      setEditingMember(null);
    },
  });

  // Remove member mutation
  const removeMemberMutation = useMutation({
    mutationFn: async (userId: string) => {
      if (!classId) throw new Error('No class selected');
      const response = await classesService.removeClassMember(classId, userId);
      if (!response.success) {
        throw new Error(response.error || 'Failed to remove member');
      }
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['class', 'members', classId] });
    },
  });

  // Import students mutation
  const importStudentsMutation = useMutation({
    mutationFn: async (userIds: string[]) => {
      if (!classId) throw new Error('No class selected');
      const response = await classesService.importStudents(classId, userIds);
      if (!response.success) {
        throw new Error(response.error || 'Failed to import students');
      }
      // Unwrap ApiResponse if needed
      if ('data' in response && response.data) {
        return response.data as ImportStudentsResponse;
      }
      return response as ImportStudentsResponse;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['class', 'members', classId] });
      setImportResults(data);
    },
  });

  const handleAddMember = () => {
    if (!addMemberForm.email && !addMemberForm.user_id) {
      return;
    }
    addMemberMutation.mutate(addMemberForm);
  };

  const handleUpdateRole = (userId: string, role: 'instructor' | 'ta' | 'student') => {
    updateMemberMutation.mutate({ userId, role });
  };

  const handleRemoveMember = (member: ClassMember) => {
    if (
      window.confirm(
        `Are you sure you want to remove ${member.display_name || member.email} from ${classId}?`
      )
    ) {
      removeMemberMutation.mutate(member.user_id);
    }
  };

  const handleImportStudents = () => {
    // Parse the text input - split by newlines, commas, or whitespace
    const userIds = importText
      .split(/[\n,\s]+/)
      .map((id) => id.trim())
      .filter((id) => id.length > 0);

    if (userIds.length === 0) {
      return;
    }

    importStudentsMutation.mutate(userIds);
  };

  const handleCloseImport = () => {
    setShowImportForm(false);
    setImportText('');
    setImportResults(null);
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      setImportText(text);
    };
    reader.readAsText(file);
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'instructor':
        return 'bg-blue-100 text-blue-800';
      case 'ta':
        return 'bg-yellow-100 text-yellow-800';
      case 'student':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const members = membersData?.members || [];

  return (
    <>
      {/* Error Display */}
      {(membersError || addMemberMutation.error || updateMemberMutation.error || removeMemberMutation.error || importStudentsMutation.error) && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {membersError instanceof Error
              ? membersError.message
              : addMemberMutation.error instanceof Error
              ? addMemberMutation.error.message
              : updateMemberMutation.error instanceof Error
              ? updateMemberMutation.error.message
              : removeMemberMutation.error instanceof Error
              ? removeMemberMutation.error.message
              : importStudentsMutation.error instanceof Error
              ? importStudentsMutation.error.message
              : 'An error occurred'}
          </AlertDescription>
        </Alert>
      )}

      {/* Add Member Form */}
      {showAddForm && (
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Add Member to {classId}</CardTitle>
            <CardDescription>Assign a user to this class with a specific role</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <Label htmlFor="email">User Email or ID</Label>
                <Input
                  id="email"
                  type="text"
                  placeholder="user@example.com or user_id"
                  value={addMemberForm.email || addMemberForm.user_id}
                  onChange={(e) =>
                    setAddMemberForm({
                      ...addMemberForm,
                      email: e.target.value,
                      user_id: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <Label htmlFor="role">Role</Label>
                <Select
                  value={addMemberForm.role}
                  onValueChange={(value: 'instructor' | 'ta' | 'student') =>
                    setAddMemberForm({ ...addMemberForm, role: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="instructor">Instructor</SelectItem>
                    <SelectItem value="ta">TA</SelectItem>
                    <SelectItem value="student">Student</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={handleAddMember}
                  disabled={addMemberMutation.isPending || !addMemberForm.email}
                >
                  {addMemberMutation.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Adding...
                    </>
                  ) : (
                    'Add Member'
                  )}
                </Button>
                <Button variant="outline" onClick={() => setShowAddForm(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Import Students Form */}
      {showImportForm && (
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="w-5 h-5" />
              Import Students to {classId}
            </CardTitle>
            <CardDescription>
              Bulk add students by importing their IDs from a CSV file or pasting them directly
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!importResults ? (
              <div className="space-y-4">
                {/* Format Guidance */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-medium text-blue-900 flex items-center gap-2 mb-2">
                    <FileText className="w-4 h-4" />
                    CSV Format Guide
                  </h4>
                  <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
                    <li>Enter one student ID per line, or separate IDs with commas</li>
                    <li>Email domains will be automatically stripped (e.g., <code className="bg-blue-100 px-1 rounded">jsmith1@jhu.edu</code> → <code className="bg-blue-100 px-1 rounded">jsmith1</code>)</li>
                    <li>IDs are case-insensitive and will be converted to lowercase</li>
                    <li>Students not in the system will be created as pending users</li>
                  </ul>
                  <div className="mt-3 p-2 bg-white rounded border border-blue-200">
                    <p className="text-xs text-blue-700 font-medium mb-1">Example:</p>
                    <pre className="text-xs text-blue-800 font-mono">jsmith1
mjohnson2
alee3@jhu.edu
bwilliams4</pre>
                  </div>
                </div>

                {/* File Upload */}
                <div>
                  <Label htmlFor="csv-file">Upload CSV File</Label>
                  <div className="mt-1">
                    <Input
                      id="csv-file"
                      type="file"
                      accept=".csv,.txt"
                      onChange={handleFileUpload}
                      className="cursor-pointer"
                    />
                  </div>
                </div>

                {/* Text Input */}
                <div>
                  <Label htmlFor="student-ids">Or paste student IDs directly</Label>
                  <textarea
                    id="student-ids"
                    className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 mt-1"
                    placeholder="Enter student IDs (one per line or comma-separated)..."
                    value={importText}
                    onChange={(e) => setImportText(e.target.value)}
                  />
                  {importText && (
                    <p className="text-sm text-muted-foreground mt-1">
                      {importText.split(/[\n,\s]+/).filter((id) => id.trim().length > 0).length} IDs detected
                    </p>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <Button
                    onClick={handleImportStudents}
                    disabled={importStudentsMutation.isPending || !importText.trim()}
                  >
                    {importStudentsMutation.isPending ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Importing...
                      </>
                    ) : (
                      <>
                        <Upload className="w-4 h-4 mr-2" />
                        Import Students
                      </>
                    )}
                  </Button>
                  <Button variant="outline" onClick={handleCloseImport}>
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              /* Import Results */
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-green-700">
                  <CheckCircle2 className="w-5 h-5" />
                  <span className="font-medium">Import Complete</span>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-green-700">{importResults.imported}</p>
                    <p className="text-sm text-green-600">Imported</p>
                  </div>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-blue-700">{importResults.created}</p>
                    <p className="text-sm text-blue-600">New Users Created</p>
                  </div>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-gray-700">{importResults.skipped}</p>
                    <p className="text-sm text-gray-600">Skipped</p>
                  </div>
                </div>

                {importResults.errors.length > 0 && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p className="font-medium text-red-800 mb-2">Errors ({importResults.errors.length})</p>
                    <ul className="text-sm text-red-700 space-y-1">
                      {importResults.errors.slice(0, 5).map((err, idx) => (
                        <li key={idx}>
                          <code className="bg-red-100 px-1 rounded">{err.user_id}</code>: {err.error}
                        </li>
                      ))}
                      {importResults.errors.length > 5 && (
                        <li className="text-red-600">...and {importResults.errors.length - 5} more errors</li>
                      )}
                    </ul>
                  </div>
                )}

                <Button onClick={handleCloseImport}>
                  Done
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Members Table */}
      <Card className="shadow-lg">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                Students
              </CardTitle>
              <CardDescription>
                {loadingMembers ? 'Loading...' : `${members.length} member(s)`}
              </CardDescription>
            </div>
            {!showAddForm && !showImportForm && (
              <div className="flex gap-2">
                <Button onClick={() => setShowAddForm(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Member
                </Button>
                <Button variant="outline" onClick={() => setShowImportForm(true)}>
                  <Upload className="w-4 h-4 mr-2" />
                  Import Students
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {loadingMembers ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin" />
              <span className="ml-2 text-lg">Loading members...</span>
            </div>
          ) : members.length === 0 ? (
            <div className="text-center py-12">
              <Users className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground text-lg mb-4">
                No members found in this class. Add your first member to get started!
              </p>
              <div className="flex gap-2 justify-center">
                <Button onClick={() => setShowAddForm(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Member
                </Button>
                <Button variant="outline" onClick={() => setShowImportForm(true)}>
                  <Upload className="w-4 h-4 mr-2" />
                  Import Students
                </Button>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-3 font-semibold">Name</th>
                    <th className="text-left p-3 font-semibold">Email</th>
                    <th className="text-left p-3 font-semibold">User ID</th>
                    <th className="text-left p-3 font-semibold">Role</th>
                    <th className="text-right p-3 font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {members.map((member: ClassMember) => (
                    <tr key={member.user_id} className="border-b hover:bg-muted/50">
                      <td className="p-3">{member.display_name || '-'}</td>
                      <td className="p-3">{member.email}</td>
                      <td className="p-3 text-sm text-muted-foreground">{member.user_id}</td>
                      <td className="p-3">
                        {editingMember === member.user_id ? (
                          <div className="flex items-center gap-2">
                            <Select
                              value={editRole}
                              onValueChange={(value: 'instructor' | 'ta' | 'student') =>
                                setEditRole(value)
                              }
                            >
                              <SelectTrigger className="w-32">
                                <SelectValue>
                                  {editRole === 'instructor' ? 'Instructor' : editRole === 'ta' ? 'TA' : 'Student'}
                                </SelectValue>
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="instructor">Instructor</SelectItem>
                                <SelectItem value="ta">TA</SelectItem>
                                <SelectItem value="student">Student</SelectItem>
                              </SelectContent>
                            </Select>
                            <Button
                              size="sm"
                              onClick={() => handleUpdateRole(member.user_id, editRole)}
                              disabled={updateMemberMutation.isPending}
                            >
                              {updateMemberMutation.isPending ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                              ) : (
                                'Save'
                              )}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setEditingMember(null)}
                            >
                              Cancel
                            </Button>
                          </div>
                        ) : (
                          <button
                            onClick={() => {
                              setEditingMember(member.user_id);
                              setEditRole(member.role);
                            }}
                            className={`px-3 py-1 rounded-full text-sm font-medium ${getRoleBadgeColor(
                              member.role
                            )} hover:opacity-80 cursor-pointer`}
                          >
                            {member.role}
                          </button>
                        )}
                      </td>
                      <td className="p-3">
                        <div className="flex justify-end gap-2">
                          <Button
                            onClick={() => handleRemoveMember(member)}
                            variant="destructive"
                            size="sm"
                            disabled={removeMemberMutation.isPending}
                          >
                            {removeMemberMutation.isPending ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <>
                                <Trash2 className="w-4 h-4 mr-1" />
                                Remove
                              </>
                            )}
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </>
  );
}
