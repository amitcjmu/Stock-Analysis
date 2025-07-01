import * as React from "react";
import { SidebarContext } from "./types";

export const SidebarContextProvider = React.createContext<SidebarContext | null>(null);

export function useSidebar() {
  const context = React.useContext(SidebarContextProvider);
  if (!context) {
    throw new Error("useSidebar must be used within a SidebarProvider.");
  }
  return context;
}