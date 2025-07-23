import React from 'react'
import type { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { UserAccessManagement } from './UserAccessManagement';
import { UserSearchAndEdit } from './UserSearchAndEdit';
import { Search, Shield, Users } from 'lucide-react';

export const UserManagementTabs: React.FC = () => {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            User Management
          </CardTitle>
          <CardDescription>
            Comprehensive user management including search, editing, and access control
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="search" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="search" className="flex items-center gap-2">
                <Search className="h-4 w-4" />
                User Search & Edit
              </TabsTrigger>
              <TabsTrigger value="access" className="flex items-center gap-2">
                <Shield className="h-4 w-4" />
                Access Management
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="search" className="mt-6">
              <UserSearchAndEdit />
            </TabsContent>
            
            <TabsContent value="access" className="mt-6">
              <UserAccessManagement />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}; 