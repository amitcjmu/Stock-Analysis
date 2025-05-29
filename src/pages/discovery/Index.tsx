import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Link } from 'react-router-dom';
import Sidebar from '../../components/Sidebar';
import FeedbackWidget from '../../components/FeedbackWidget';
import { Database, Server, HardDrive, Activity, ArrowRight, Sparkles, BarChart3, LayoutDashboard, Settings } from 'lucide-react';

const DiscoveryIndex = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Redirect to the discovery overview
    navigate('/discovery/overview', { replace: true });
  }, [navigate]);

  const summaryCards = [
    { title: 'Total Apps Discovered', value: '250', subtitle: 'Applications', icon: Database, color: 'bg-blue-500' },
    { title: 'Total Servers Discovered', value: '500', subtitle: 'Servers', icon: Server, color: 'bg-green-500' },
    { title: 'Databases Discovered', value: '50', subtitle: 'Databases', icon: HardDrive, color: 'bg-purple-500' },
    { title: 'Scanning Progress', value: '75%', subtitle: 'Complete', icon: Activity, color: 'bg-orange-500' }
  ];

  const quickActions = [
    { 
      title: 'Discovery Dashboard', 
      description: 'Complete landscape view and modernization readiness', 
      path: '/discovery/dashboard',
      icon: LayoutDashboard,
      color: 'bg-blue-500'
    },
    { 
      title: 'CMDB Import', 
      description: 'Import and analyze CMDB data with AI validation', 
      path: '/discovery/cmdb-import',
      icon: Database,
      color: 'bg-green-500'
    },
    { 
      title: 'Asset Inventory', 
      description: 'Browse discovered assets and their details', 
      path: '/discovery/inventory',
      icon: Server,
      color: 'bg-purple-500'
    },
    { 
      title: 'Data Cleansing', 
      description: 'Human-in-the-loop data quality improvement', 
      path: '/discovery/data-cleansing',
      icon: Sparkles,
      color: 'bg-yellow-500'
    },
    { 
      title: 'Attribute Mapping', 
      description: 'Train AI crew on field mappings and associations', 
      path: '/discovery/attribute-mapping',
      icon: Settings,
      color: 'bg-indigo-500'
    },
    { 
      title: 'Tech Debt Analysis', 
      description: 'Analyze technology stack support and modernization needs', 
      path: '/discovery/tech-debt-analysis',
      icon: BarChart3,
      color: 'bg-red-500'
    },
    { 
      title: 'Dependency Map', 
      description: 'Explore relationships between assets', 
      path: '/discovery/dependencies',
      icon: Activity,
      color: 'bg-teal-500'
    },
    { 
      title: 'Scanning Status', 
      description: 'Monitor ongoing discovery scans', 
      path: '/discovery/scan',
      icon: Activity,
      color: 'bg-orange-500'
    }
  ];

  const discoveryPhases = [
    {
      phase: 'Data Collection',
      description: 'Gather data from CMDB, monitoring tools, and code scans',
      actions: ['CMDB Import', 'Scanning Status'],
      status: 'completed',
      color: 'bg-green-100 text-green-800'
    },
    {
      phase: 'Data Quality & Cleansing',
      description: 'Clean and validate discovered data with AI assistance',
      actions: ['Data Cleansing', 'Attribute Mapping'],
      status: 'in_progress',
      color: 'bg-yellow-100 text-yellow-800'
    },
    {
      phase: 'Analysis & Assessment',
      description: 'Analyze tech stack, dependencies, and modernization readiness',
      actions: ['Tech Debt Analysis', 'Dependency Map'],
      status: 'pending',
      color: 'bg-gray-100 text-gray-800'
    },
    {
      phase: 'Landscape Overview',
      description: 'Complete view of IT landscape for cloud planning',
      actions: ['Discovery Dashboard', 'Asset Inventory'],
      status: 'ready',
      color: 'bg-blue-100 text-blue-800'
    }
  ];

  return null;
};

export default DiscoveryIndex;
