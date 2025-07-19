/**
 * Sidebar Components - Index
 * 
 * Centralized exports for all sidebar components and utilities.
 * This module provides a complete sidebar system with context management,
 * layout components, menu structures, and interactive elements.
 */

// Context and hook
export { SidebarContext, useSidebar } from './sidebar-context'

// Provider
export { SidebarProvider } from './sidebar-provider'

// Core components
export { Sidebar, SidebarInset } from './sidebar-core'

// Interaction components
export { SidebarTrigger, SidebarRail } from './sidebar-interactions'

// Layout components
export { 
  SidebarHeader, 
  SidebarFooter, 
  SidebarContent, 
  SidebarInput, 
  SidebarSeparator 
} from './sidebar-layout'

// Group components
export { 
  SidebarGroup, 
  SidebarGroupLabel, 
  SidebarGroupAction, 
  SidebarGroupContent 
} from './sidebar-group'

// Menu components
export { 
  SidebarMenu, 
  SidebarMenuItem, 
  SidebarMenuButton, 
  SidebarMenuAction, 
  SidebarMenuBadge, 
  SidebarMenuSkeleton 
} from './sidebar-menu'

// Sub-menu components
export { 
  SidebarMenuSub, 
  SidebarMenuSubItem, 
  SidebarMenuSubButton 
} from './sidebar-submenu'

// Constants
export * from './sidebar-constants'