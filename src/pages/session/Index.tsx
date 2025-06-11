import React from 'react';
import { useSessions } from '@/contexts/SessionContext';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';

const SessionIndexPage: React.FC = () => {
    const { data: sessions = [], isLoading, error } = useSessions();

    if (isLoading) {
        return <div>Loading sessions...</div>;
    }

    if (error) {
        return <div className="text-red-500">Error: {error.message}</div>;
    }

    return (
        <div className="container mx-auto p-4">
            <div className="flex justify-between items-center mb-4">
                <h1 className="text-2xl font-bold">Session Management</h1>
                <Button asChild>
                    <Link to="/sessions/new">Create New Session</Link>
                </Button>
            </div>
            
            <div className="bg-white shadow rounded-lg">
                <ul className="divide-y divide-gray-200">
                    {sessions.length > 0 ? (
                        sessions.map(session => (
                            <li key={session.id} className="p-4 flex justify-between items-center">
                                <div>
                                    <p className="font-semibold">{session.name}</p>
                                    <p className="text-sm text-gray-500">ID: {session.id}</p>
                                </div>
                                <div>
                                    {session.is_default && (
                                        <span className="text-xs bg-green-100 text-green-800 rounded-full px-2 py-1">
                                            Default
                                        </span>
                                    )}
                                    <Button variant="outline" size="sm" className="ml-4" asChild>
                                        <Link to={`/sessions/${session.id}/edit`}>Edit</Link>
                                    </Button>
                                </div>
                            </li>
                        ))
                    ) : (
                        <li className="p-4 text-center text-gray-500">No sessions found.</li>
                    )}
                </ul>
            </div>
        </div>
    );
};

export default SessionIndexPage;
