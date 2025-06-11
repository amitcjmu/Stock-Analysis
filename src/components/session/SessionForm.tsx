import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Loader2 } from 'lucide-react';
import { useCreateSession, useUpdateSession, UISession } from '@/contexts/SessionContext';

// Define form schema
export const sessionFormSchema = z.object({
  name: z.string().min(3, 'Display name must be at least 3 characters'),
  session_type: z.enum(['analysis', 'migration', 'testing', 'other']).default('analysis'),
  is_default: z.boolean().default(false),
});

export type SessionFormValues = z.infer<typeof sessionFormSchema>;

interface SessionFormProps {
  sessionToEdit?: UISession;
  onSuccess?: () => void;
}

export const SessionFormComponent: React.FC<SessionFormProps> = ({
  sessionToEdit,
  onSuccess,
}) => {
  const createSessionMutation = useCreateSession();
  const updateSessionMutation = useUpdateSession();

  const isEditing = !!sessionToEdit;
  const isSubmitting = createSessionMutation.isPending || updateSessionMutation.isPending;

  const form = useForm<SessionFormValues>({
    resolver: zodResolver(sessionFormSchema),
    defaultValues: {
      name: '',
      is_default: false,
      session_type: 'analysis',
    },
  });

  useEffect(() => {
    if (sessionToEdit) {
      form.reset({
        name: sessionToEdit.name,
        is_default: sessionToEdit.is_default,
        session_type: sessionToEdit.session_type || 'analysis',
      });
    } else {
      form.reset({
        name: '',
        is_default: false,
        session_type: 'analysis',
      });
    }
  }, [sessionToEdit, form]);

  const onSubmit = async (formData: SessionFormValues) => {
    try {
      if (isEditing && sessionToEdit) {
        await updateSessionMutation.mutateAsync({ 
            sessionId: sessionToEdit.id, 
            updates: formData 
        });
      } else {
        await createSessionMutation.mutateAsync({ 
            name: formData.name, 
            isDefault: formData.is_default 
        });
      }
      onSuccess?.();
    } catch (error) {
      // Errors are handled by the hooks' onError callbacks
      console.error('Failed to save session:', error);
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Display Name *</FormLabel>
                <FormControl>
                  <Input placeholder="e.g., Q3 Planning" {...field} />
                </FormControl>
                <FormDescription>The display name shown in the UI.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="session_type"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Session Type</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a session type" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="analysis">Analysis</SelectItem>
                    <SelectItem value="migration">Migration</SelectItem>
                    <SelectItem value="testing">Testing</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
                <FormDescription>The type of session you're creating.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="is_default"
            render={({ field }) => (
              <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                <div className="space-y-0.5">
                  <FormLabel className="text-base">Default Session</FormLabel>
                  <FormDescription>
                    Set this as your default session for this engagement.
                  </FormDescription>
                </div>
                <FormControl>
                  <Switch
                    checked={field.value}
                    onCheckedChange={field.onChange}
                    aria-label="Set as default session"
                  />
                </FormControl>
              </FormItem>
            )}
          />

        <div className="flex justify-end space-x-4">
          <Button
            type="button"
            variant="outline"
            onClick={onSuccess}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={isSubmitting || !form.formState.isDirty}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {isEditing ? 'Saving...' : 'Creating...'}
              </>
            ) : isEditing ? (
              'Save Changes'
            ) : (
              'Create Session'
            )}
          </Button>
        </div>
      </form>
    </Form>
  );
}
