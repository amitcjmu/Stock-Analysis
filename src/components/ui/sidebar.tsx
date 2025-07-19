/**
 * Sidebar Components
 * 
 * Comprehensive sidebar system with context management, layout components, 
 * menu structures, and interactive elements.
 * 
 * This file has been modularized for better maintainability.
 * Individual modules are located in ./sidebar/ directory.
 */

// Import and re-export from the modular structure
import { SidebarProvider } from './sidebar/sidebar-provider';
import { SidebarContext, useSidebar } from './sidebar/sidebar-context';
import { Sidebar, SidebarInset } from './sidebar/sidebar-core';
import { SidebarTrigger, SidebarRail } from './sidebar/sidebar-interactions';
import { 
  SidebarHeader, 
  SidebarFooter, 
  SidebarContent, 
  SidebarInput, 
  SidebarSeparator 
} from './sidebar/sidebar-layout';
import { 
  SidebarGroup, 
  SidebarGroupLabel, 
  SidebarGroupAction, 
  SidebarGroupContent 
} from './sidebar/sidebar-group';
import { 
  SidebarMenu, 
  SidebarMenuItem, 
  SidebarMenuButton, 
  SidebarMenuAction, 
  SidebarMenuBadge, 
  SidebarMenuSkeleton 
} from './sidebar/sidebar-menu';
import { 
  SidebarMenuSub, 
  SidebarMenuSubItem, 
  SidebarMenuSubButton 
} from './sidebar/sidebar-submenu';

// Re-export everything
export {
  // Provider and context
  SidebarProvider,
  SidebarContext,
  useSidebar,
  
  // Core components
  Sidebar,
  SidebarInset,
  
  // Interaction components
  SidebarTrigger,
  SidebarRail,
  
  // Layout components
  SidebarHeader,
  SidebarFooter,
  SidebarContent,
  SidebarInput,
  SidebarSeparator,
  
  // Group components
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupAction,
  SidebarGroupContent,
  
  // Menu components
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarMenuAction,
  SidebarMenuBadge,
  SidebarMenuSkeleton,
  
  // Sub-menu components
  SidebarMenuSub,
  SidebarMenuSubItem,
  SidebarMenuSubButton
};

// Re-export constants and types
export * from './sidebar/sidebar-constants';
