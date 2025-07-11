# Modular Sidebar Components

This directory contains the modular sidebar components that were refactored from the original monolithic `Sidebar.tsx` component (697 LOC).

## Architecture Overview

The sidebar has been decomposed into 6 specialized components, each handling specific aspects of the sidebar functionality:

```
Sidebar (Main Composition)
├── SidebarHeader (Brand & Authentication)
├── NavigationMenu (Main Navigation)
│   ├── ExpandableMenuSection (Submenu Sections)
│   └── NavigationItem (Individual Menu Items)
├── AuthenticationIndicator (User Profile Link)
└── VersionDisplay (Version & Feedback)
```

## Component Breakdown

### 1. SidebarHeader
**File:** `SidebarHeader.tsx`  
**Purpose:** Header with logo, brand, and authentication state  
**Features:**
- Brand display with AI Force logo
- Authentication state visualization via icon color
- Click-to-login/logout functionality
- Hover effects and transitions

### 2. NavigationMenu
**File:** `NavigationMenu.tsx`  
**Purpose:** Main navigation structure and routing  
**Features:**
- Renders complete navigation hierarchy
- Manages active route highlighting
- Handles submenu expansion states
- Coordinates between navigation items and sections

### 3. ExpandableMenuSection
**File:** `ExpandableMenuSection.tsx`  
**Purpose:** Submenu expansion logic and accordion behavior  
**Features:**
- Accordion-style submenu expansion
- Chevron icon rotation animation
- Parent active state management
- Submenu item rendering

### 4. NavigationItem
**File:** `NavigationItem.tsx`  
**Purpose:** Individual navigation item component  
**Features:**
- Flexible styling for main and sub-items
- Active state handling
- Icon and label rendering
- React Router Link integration

### 5. AuthenticationIndicator
**File:** `AuthenticationIndicator.tsx`  
**Purpose:** User authentication status and profile access  
**Features:**
- Conditional rendering based on auth state
- User profile navigation link
- Clean authentication UI

### 6. VersionDisplay
**File:** `VersionDisplay.tsx`  
**Purpose:** Version information and feedback access  
**Features:**
- Version number display
- Feedback link functionality
- Hover effects and styling

## TypeScript Types

All components use strict TypeScript typing defined in `types.ts`:

```typescript
interface NavigationItem {
  name: string;
  path: string;
  icon: LucideIcon;
  hasSubmenu?: boolean;
  submenu?: NavigationItem[];
}

interface SidebarProps {
  className?: string;
}

interface ExpandedStates {
  discovery: boolean;
  assess: boolean;
  plan: boolean;
  execute: boolean;
  modernize: boolean;
  decommission: boolean;
  finops: boolean;
  observability: boolean;
  admin: boolean;
}
```

## Main Sidebar Component

The main `Sidebar.tsx` component serves as the composition root:

```typescript
const Sidebar: React.FC<SidebarProps> = ({ className }) => {
  // State management
  const [expandedStates, setExpandedStates] = useState<ExpandedStates>({...});
  
  // Event handlers
  const handleToggleExpanded = (sectionName: string) => {...};
  const handleAuthClick = () => {...};
  const handleVersionClick = () => {...};

  return (
    <div className={`fixed left-0 top-0 h-full w-64 bg-gray-800 text-white z-40 ${className || ''}`}>
      <SidebarHeader {...headerProps} />
      <NavigationMenu {...menuProps} />
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-700">
        <AuthenticationIndicator {...authProps} />
        <VersionDisplay {...versionProps} />
      </div>
    </div>
  );
};
```

## Usage

### Basic Usage
```typescript
import { Sidebar } from './components/layout/sidebar';

function App() {
  return (
    <div className="app">
      <Sidebar />
      <main className="main-content">
        {/* Main content */}
      </main>
    </div>
  );
}
```

### With Custom Styling
```typescript
<Sidebar className="custom-sidebar-styling" />
```

### Individual Component Usage
```typescript
import { 
  SidebarHeader, 
  NavigationMenu, 
  ExpandableMenuSection 
} from './components/layout/sidebar';

// Use components individually if needed
<SidebarHeader onAuthClick={handleAuth} isAuthenticated={true} />
```

## State Management

The sidebar manages several types of state:

1. **Navigation State**: Current path and active routes
2. **Expansion State**: Which submenus are expanded
3. **Authentication State**: User authentication status
4. **UI State**: Loading states, hover effects

## Performance Considerations

- **Memoization**: Components use React hooks effectively
- **Event Handling**: Efficient event delegation
- **Conditional Rendering**: Smart conditional rendering to reduce DOM operations
- **Type Safety**: Full TypeScript coverage prevents runtime errors

## Accessibility Features

- **Keyboard Navigation**: Full keyboard support
- **Screen Reader Support**: Proper ARIA labels and roles
- **Focus Management**: Logical tab order
- **Color Contrast**: Sufficient color contrast ratios

## Migration Notes

The original `Sidebar.tsx` (697 LOC) has been completely refactored into this modular system while maintaining:

- **✅ 100% Functional Parity**: All original functionality preserved
- **✅ Same Component API**: Drop-in replacement
- **✅ Identical Styling**: CSS classes and styles maintained
- **✅ State Management**: All state behavior preserved
- **✅ Event Handling**: All event handlers working
- **✅ TypeScript Safety**: Improved type safety

## Benefits of Modularization

1. **Maintainability**: Each component has a single responsibility
2. **Reusability**: Components can be used independently
3. **Testability**: Easier to unit test individual components
4. **Readability**: Smaller, focused components are easier to understand
5. **Scalability**: Easy to add new features to specific components
6. **Type Safety**: Better TypeScript inference and error detection

## File Structure

```
src/components/layout/sidebar/
├── index.ts                     # Main exports
├── types.ts                     # TypeScript type definitions
├── Sidebar.tsx                  # Main composition component
├── SidebarHeader.tsx           # Brand and authentication header
├── NavigationMenu.tsx          # Main navigation structure
├── ExpandableMenuSection.tsx   # Submenu expansion logic
├── NavigationItem.tsx          # Individual navigation items
├── AuthenticationIndicator.tsx # User authentication status
├── VersionDisplay.tsx          # Version and feedback display
└── README.md                   # This documentation
```

## Testing

Each component should be tested individually:

```typescript
// Example test for NavigationItem
import { render, screen } from '@testing-library/react';
import { NavigationItem } from './NavigationItem';

test('renders navigation item with correct link', () => {
  render(
    <NavigationItem 
      item={{ name: 'Dashboard', path: '/', icon: Home }}
      isActive={false}
    />
  );
  
  expect(screen.getByText('Dashboard')).toBeInTheDocument();
});
```

## Contributing

When adding new features:

1. **Single Responsibility**: Keep each component focused
2. **Type Safety**: Add proper TypeScript types
3. **Accessibility**: Ensure ARIA compliance
4. **Documentation**: Update README and inline docs
5. **Testing**: Add appropriate tests
6. **Consistency**: Follow existing patterns and conventions