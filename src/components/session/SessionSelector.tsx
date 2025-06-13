import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useSession } from '@/contexts/SessionContext';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue, SelectGroup, SelectLabel } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { PlusCircle, MoreVertical } from "lucide-react";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useToast } from '../ui/use-toast';

export const SessionSelector: React.FC = () => {
    const { toast } = useToast();
    const { user } = useAuth();
    const { 
        currentSession,
        sessions,
        isLoading,
        error,
        createSession,
        switchSession
    } = useSession();

    const [isCreateDialogOpen, setCreateDialogOpen] = useState(false);
    const [newSessionName, setNewSessionName] = useState("");
    const [isDefault, setIsDefault] = useState(false);

    useEffect(() => {
        // If there's no current session but there are sessions available, set one.
        // Prioritize the default session, otherwise take the first one.
        if (!currentSession && sessions.length > 0 && !isLoading) {
            const defaultSession = sessions.find(s => s.is_default) || sessions[0];
            if (defaultSession) {
                switchSession(defaultSession.id);
            }
        }
    }, [sessions, currentSession, isLoading, switchSession]);

    const handleCreateSession = async () => {
        if (!newSessionName.trim()) {
            toast({ title: "Session name is required", variant: "destructive" });
            return;
        }
        try {
            await createSession(newSessionName, isDefault);
            setNewSessionName("");
            setIsDefault(false);
            setCreateDialogOpen(false);
        } catch (e) {
            // Error is already handled by the mutation's onError
        }
    };

    if (!user) {
        return (
            <div className="flex items-center space-x-2">
                <Select disabled>
                    <SelectTrigger className="w-[200px] h-9">
                        <SelectValue placeholder="Not Authenticated" />
                    </SelectTrigger>
                </Select>
            </div>
        );
    }

    if (isLoading) {
        return <div>Loading sessions...</div>;
    }

    if (error) {
        return <div>Error loading sessions: {error.message}</div>;
    }

    return (
        <div className="flex items-center space-x-2">
            <Select
                value={currentSession?.id || ""}
                onValueChange={(value) => switchSession(value)}
                disabled={sessions.length === 0}
            >
                <SelectTrigger className="w-[200px] h-9">
                    <SelectValue placeholder="Select a session..." />
                </SelectTrigger>
                <SelectContent>
                    <SelectGroup>
                        <SelectLabel>Available Sessions</SelectLabel>
                        {sessions.map((session) => (
                            <SelectItem key={session.id} value={session.id}>
                                {session.name}{session.is_default ? ' (Default)' : ''}
                            </SelectItem>
                        ))}
                    </SelectGroup>
                </SelectContent>
            </Select>

            <Dialog open={isCreateDialogOpen} onOpenChange={setCreateDialogOpen}>
                <DialogTrigger asChild>
                    <Button variant="outline" size="sm" className="h-9">
                        <PlusCircle className="mr-2 h-4 w-4" />
                        New Session
                    </Button>
                </DialogTrigger>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Create New Session</DialogTitle>
                        <DialogDescription>
                            Enter a name for your new session. You can optionally set it as the default for this engagement.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="session-name" className="text-right">
                                Name
                            </Label>
                            <Input
                                id="session-name"
                                value={newSessionName}
                                onChange={(e) => setNewSessionName(e.target.value)}
                                className="col-span-3"
                                placeholder="e.g., Q3 Planning"
                            />
                        </div>
                        <div className="flex items-center space-x-2 ml-auto">
                            <Checkbox
                                id="is-default"
                                checked={isDefault}
                                onCheckedChange={(checked) => setIsDefault(checked as boolean)}
                            />
                            <Label htmlFor="is-default">Set as default</Label>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button
                            type="submit"
                            onClick={handleCreateSession}
                            disabled={isLoading}
                        >
                            {isLoading ? "Creating..." : "Create Session"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {currentSession && (
                 <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" className="h-9 px-2">
                            <MoreVertical className="h-4 w-4" />
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent>
                        {/* Add rename/delete options here if needed */}
                    </DropdownMenuContent>
                </DropdownMenu>
            )}
        </div>
    );
};

export default SessionSelector;
