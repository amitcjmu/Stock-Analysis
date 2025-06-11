import { useParams, useNavigate } from 'react-router-dom';
import { useToast } from '@/components/ui/use-toast';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft } from 'lucide-react';
import { SessionFormComponent } from '@/components/session/SessionForm';
import { useSessions } from '@/contexts/SessionContext';
import { useAuth } from '@/contexts/AuthContext';

export default function SessionFormPage() {
    const { id } = useParams<{ id?: string }>();
    const navigate = useNavigate();
    const { toast } = useToast();
    const { currentSessionId } = useAuth();
    const { data: sessions = [], isLoading } = useSessions();
    
    const isEditing = !!id;
    const sessionToEdit = isEditing 
        ? sessions?.find(s => s.id === id) 
        : undefined;

    const handleSuccess = () => {
        toast({
            title: isEditing ? 'Session updated' : 'Session created',
            description: isEditing 
                ? 'Your session has been updated successfully.'
                : 'Your new session has been created.',
        });
        navigate('/sessions'); // Navigate back to the session list
    };

    if (isLoading) {
        return <div>Loading session data...</div>;
    }

    // This check might need to be adjusted based on new auth flow
    if (!currentSessionId && !isEditing) {
        return (
            <div className="container mx-auto py-8">
                <div className="flex flex-col items-center justify-center space-y-4">
                    <h2 className="text-2xl font-bold">No active session</h2>
                    <p className="text-muted-foreground">Please select an engagement first.</p>
                    <Button onClick={() => navigate('/admin/engagements')}>Go to Engagements</Button>
                </div>
            </div>
        );
    }

    return (
        <div className="container mx-auto py-8">
            <div className="mb-6">
                <Button 
                    variant="ghost" 
                    className="pl-0"
                    onClick={() => navigate(-1)}
                >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back to Sessions
                </Button>
            </div>

            <div className="max-w-3xl mx-auto">
                <Card>
                    <CardHeader>
                        <CardTitle>
                            {isEditing ? 'Edit Session' : 'Create New Session'}
                        </CardTitle>
                        <CardDescription>
                            {isEditing 
                                ? 'Update the details of your session.'
                                : 'Create a new session to organize your migration work.'}
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <SessionFormComponent 
                            sessionToEdit={sessionToEdit}
                            onSuccess={handleSuccess} 
                        />
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
