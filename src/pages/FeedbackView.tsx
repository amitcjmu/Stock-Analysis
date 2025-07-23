import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import { Filter, ThumbsUp } from 'lucide-react'
import { MessageSquare, Clock, User, Search, Star, AlertTriangle, CheckCircle } from 'lucide-react'
import { apiCall, API_CONFIG } from '../config/api';

interface FeedbackItem {
  id: string;
  page: string;
  rating: number;
  comment: string;
  timestamp: string;
  userAgent?: string;
  status: 'new' | 'reviewed' | 'resolved';
  category: 'ui' | 'performance' | 'feature' | 'bug' | 'general';
}

const FeedbackView: React.FC = () => {
  const [feedback, setFeedback] = useState<FeedbackItem[]>([]);
  const [filteredFeedback, setFilteredFeedback] = useState<FeedbackItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [selectedPage, setSelectedPage] = useState('all');
  const [selectedRating, setSelectedRating] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const [summary, setSummary] = useState({
    total: 0,
    avgRating: 0,
    byStatus: { new: 0, reviewed: 0, resolved: 0 },
    byPage: {} as Record<string, number>,
    byRating: {} as Record<string, number>
  });

  useEffect(() => {
    fetchFeedback();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [feedback, selectedPage, selectedRating, selectedStatus, selectedCategory, searchTerm]);

  const fetchFeedback = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Debug: Log the API configuration
      console.log('🔍 API Configuration Debug:');
      console.log('BASE_URL:', API_CONFIG.BASE_URL);
      console.log('FEEDBACK Endpoint:', API_CONFIG.ENDPOINTS.DISCOVERY.FEEDBACK);
      console.log('Full URL:', `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.DISCOVERY.FEEDBACK}`);
      console.log('Environment Variables:');
      console.log('- VITE_BACKEND_URL:', import.meta.env.VITE_BACKEND_URL);
      console.log('- VITE_API_BASE_URL:', import.meta.env.VITE_API_BASE_URL);
      console.log('- MODE:', import.meta.env.MODE);
      console.log('- PROD:', import.meta.env.PROD);
      console.log('- Window location:', typeof window !== 'undefined' ? window.location.href : 'SSR');

      // Try to fetch from actual API first
      const response = await apiCall('discovery/feedback');
      console.log('API Response:', response); // Debug log
      
      const allFeedback = response.feedback || [];
      
      // Filter for page feedback only (exclude CMDB analysis feedback)
      const pageFeedback = allFeedback.filter((item: unknown) => 
        item.feedback_type === 'page_feedback' || 
        (!item.feedback_type && item.page && item.rating && item.comment)
      );
      
      // Transform the data to match our expected format
      const transformedFeedback: FeedbackItem[] = pageFeedback.map((item: unknown) => ({
        id: item.id || Math.random().toString(),
        page: item.page || 'Unknown',
        rating: item.rating || 0,
        comment: item.comment || '',
        timestamp: item.user_timestamp || item.timestamp || new Date().toISOString(),
        userAgent: item.userAgent,
        status: item.status || 'new',
        category: item.category || 'general'
      }));
      
      setFeedback(transformedFeedback);
      
      // Calculate summary from feedback data
      if (transformedFeedback.length > 0) {
        const total = transformedFeedback.length;
        const avgRating = transformedFeedback.reduce((sum: number, f: FeedbackItem) => sum + f.rating, 0) / total;
        const byStatus = transformedFeedback.reduce((acc: unknown, f: FeedbackItem) => {
          acc[f.status] = (acc[f.status] || 0) + 1;
          return acc;
        }, {} as Record<string, number>);
        const byPage = transformedFeedback.reduce((acc: unknown, f: FeedbackItem) => {
          acc[f.page] = (acc[f.page] || 0) + 1;
          return acc;
        }, {} as Record<string, number>);
        const byRating = transformedFeedback.reduce((acc: unknown, f: FeedbackItem) => {
          const rating = f.rating.toString();
          acc[rating] = (acc[rating] || 0) + 1;
          return acc;
        }, {} as Record<string, number>);

        setSummary({ 
          total, 
          avgRating, 
          byStatus: {
            new: byStatus['new'] || 0,
            reviewed: byStatus['reviewed'] || 0,
            resolved: byStatus['resolved'] || 0
          },
          byPage,
          byRating 
        });
      } else {
        // Set empty summary if no feedback
        setSummary({
          total: 0,
          avgRating: 0,
          byStatus: { new: 0, reviewed: 0, resolved: 0 },
          byPage: {},
          byRating: {}
        });
      }
      
      console.log('Processed feedback:', transformedFeedback); // Debug log
      
    } catch (error) {
      console.error('Failed to fetch feedback:', error);
      console.error('Error details:', {
        name: error?.name,
        message: error?.message,
        stack: error?.stack
      });
      
      setError(`Failed to load feedback data: ${error}`);
      
      // In production, always show demo data as fallback for better UX
      if (import.meta.env.PROD || import.meta.env.DEV) {
        console.warn('Using demo data as fallback');
        generateDemoFeedback();
      }
    } finally {
      setIsLoading(false);
    }
  };

  const generateDemoFeedback = () => {
    const demoFeedback: FeedbackItem[] = [
      {
        id: '1',
        page: 'Asset Inventory',
        rating: 4,
        comment: 'The app dependencies dropdown is now working great with the refresh button! Makes it much easier to see which applications are mapped to servers. The 10 per page pagination is perfect too.',
        timestamp: '2025-01-28T15:45:00Z',
        status: 'resolved',
        category: 'feature'
      },
      {
        id: '2', 
        page: 'Discovery > CMDB Import',
        rating: 5,
        comment: 'AI field mapping is incredible. It automatically detected our custom field names like "CI_Name" and "Sys_Class" from ServiceNow. Saved hours of manual mapping work.',
        timestamp: '2025-01-28T12:30:00Z',
        status: 'reviewed',
        category: 'feature'
      },
      {
        id: '3',
        page: 'Chat Interface',
        rating: 5,
        comment: 'The chat/feedback dual interface is brilliant! Love that I can get AI help on migration questions and submit feedback without switching windows. Gemma responses are very focused and helpful.',
        timestamp: '2025-01-28T11:20:00Z',
        status: 'new',
        category: 'ui'
      },
      {
        id: '4',
        page: 'Asset Inventory',
        rating: 3,
        comment: 'The edit functionality saves properly now and the page refreshes automatically. Much better than before when changes weren\'t visible until manual refresh.',
        timestamp: '2025-01-27T16:45:00Z',
        status: 'resolved',
        category: 'bug'
      },
      {
        id: '5',
        page: 'Discovery > CMDB Import',
        rating: 4,
        comment: 'Upload process handles our 2000+ row inventory files well. Processing time is reasonable and error reporting is clear when there are data issues.',
        timestamp: '2025-01-27T09:15:00Z',
        status: 'reviewed',
        category: 'performance'
      },
      {
        id: '6',
        page: 'Asset Inventory > App Dependencies',
        rating: 4,
        comment: 'Application mapping works well for most servers. The intelligent naming pattern detection caught our HR and Finance servers automatically. Would like to see more patterns for database servers.',
        timestamp: '2025-01-26T14:30:00Z',
        status: 'new',
        category: 'feature'
      },
      {
        id: '7',
        page: 'Feedback View',
        rating: 5,
        comment: 'This centralized feedback view is exactly what we needed! Much better than scattered feedback forms. The filtering and search make it easy to track issues.',
        timestamp: '2025-01-26T13:20:00Z',
        status: 'new',
        category: 'ui'
      },
      {
        id: '8',
        page: 'Asset Inventory',
        rating: 2,
        comment: 'Initial load was showing demo data instead of our uploaded CMDB. Had to refresh several times before real data appeared. Might be a caching issue.',
        timestamp: '2025-01-25T10:45:00Z',
        status: 'reviewed',
        category: 'bug'
      }
    ];

    setFeedback(demoFeedback);
    
    // Calculate summary
    const total = demoFeedback.length;
    const avgRating = demoFeedback.reduce((sum, f) => sum + f.rating, 0) / total;
    const byStatus = demoFeedback.reduce((acc, f) => {
      acc[f.status] = (acc[f.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    const byPage = demoFeedback.reduce((acc, f) => {
      acc[f.page] = (acc[f.page] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    const byRating = demoFeedback.reduce((acc, f) => {
      const rating = f.rating.toString();
      acc[rating] = (acc[rating] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    setSummary({ 
      total, 
      avgRating, 
      byStatus: {
        new: byStatus['new'] || 0,
        reviewed: byStatus['reviewed'] || 0,
        resolved: byStatus['resolved'] || 0
      },
      byPage,
      byRating 
    });
  };

  const applyFilters = () => {
    let filtered = feedback;

    if (selectedPage !== 'all') {
      filtered = filtered.filter(f => f.page === selectedPage);
    }

    if (selectedRating !== 'all') {
      filtered = filtered.filter(f => f.rating.toString() === selectedRating);
    }

    if (selectedStatus !== 'all') {
      filtered = filtered.filter(f => f.status === selectedStatus);
    }

    if (selectedCategory !== 'all') {
      filtered = filtered.filter(f => f.category === selectedCategory);
    }

    if (searchTerm) {
      filtered = filtered.filter(f => 
        f.comment.toLowerCase().includes(searchTerm.toLowerCase()) ||
        f.page.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredFeedback(filtered);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'new': return 'bg-blue-100 text-blue-800';
      case 'reviewed': return 'bg-yellow-100 text-yellow-800';
      case 'resolved': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'ui': return <User className="h-4 w-4" />;
      case 'performance': return <Clock className="h-4 w-4" />;
      case 'feature': return <Star className="h-4 w-4" />;
      case 'bug': return <AlertTriangle className="h-4 w-4" />;
      default: return <MessageSquare className="h-4 w-4" />;
    }
  };

  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`h-4 w-4 ${i < rating ? 'text-yellow-400 fill-current' : 'text-gray-300'}`}
      />
    ));
  };

  const getUniqueValues = (field: keyof FeedbackItem) => {
    const values = Array.from(new Set(feedback.map(f => f[field])));
    return values.filter(v => v !== undefined && v !== null);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading feedback...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">User Feedback Center</h1>
              <p className="mt-2 text-gray-600">
                Comprehensive view of user feedback across all platform pages
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-500">
                Last updated: {new Date().toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <MessageSquare className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Feedback</p>
                <p className="text-2xl font-bold text-gray-900">{summary.total}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <Star className="h-8 w-8 text-yellow-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Average Rating</p>
                <p className="text-2xl font-bold text-gray-900">{(summary.avgRating || 0).toFixed(1)}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <AlertTriangle className="h-8 w-8 text-orange-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Needs Attention</p>
                <p className="text-2xl font-bold text-gray-900">{summary.byStatus.new || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <CheckCircle className="h-8 w-8 text-green-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Resolved</p>
                <p className="text-2xl font-bold text-gray-900">{summary.byStatus.resolved || 0}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Filters</h3>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
              {/* Search */}
              <div className="lg:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search feedback..."
                    className="pl-10 w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Page Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Page</label>
                <select
                  value={selectedPage}
                  onChange={(e) => setSelectedPage(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Pages</option>
                  {getUniqueValues('page').map(page => (
                    <option key={page} value={page}>{page}</option>
                  ))}
                </select>
              </div>

              {/* Rating Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Rating</label>
                <select
                  value={selectedRating}
                  onChange={(e) => setSelectedRating(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Ratings</option>
                  {[5, 4, 3, 2, 1].map(rating => (
                    <option key={rating} value={rating.toString()}>{rating} Stars</option>
                  ))}
                </select>
              </div>

              {/* Status Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Status</option>
                  <option value="new">New</option>
                  <option value="reviewed">Reviewed</option>
                  <option value="resolved">Resolved</option>
                </select>
              </div>

              {/* Category Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Categories</option>
                  <option value="ui">UI/UX</option>
                  <option value="performance">Performance</option>
                  <option value="feature">Feature</option>
                  <option value="bug">Bug</option>
                  <option value="general">General</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Feedback Items */}
        <div className="space-y-6">
          {filteredFeedback.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No feedback found</h3>
              <p className="text-gray-600">
                {searchTerm || selectedPage !== 'all' || selectedRating !== 'all' || selectedStatus !== 'all' || selectedCategory !== 'all'
                  ? 'Try adjusting your filters to see more results.'
                  : 'No feedback has been submitted yet.'}
              </p>
            </div>
          ) : (
            filteredFeedback.map((item) => (
              <div key={item.id} className="bg-white rounded-lg shadow hover:shadow-md transition-shadow">
                <div className="p-6">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="flex items-center space-x-2">
                        {getCategoryIcon(item.category)}
                        <span className="text-sm font-medium text-gray-600 capitalize">{item.category}</span>
                      </div>
                      <span className="text-gray-300">•</span>
                      <span className="text-sm font-medium text-blue-600">{item.page}</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="flex items-center space-x-1">
                        {renderStars(item.rating)}
                      </div>
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(item.status)}`}>
                        {item.status}
                      </span>
                    </div>
                  </div>

                  {/* Content */}
                  <div className="mb-4">
                    <p className="text-gray-800 leading-relaxed">{item.comment}</p>
                  </div>

                  {/* Footer */}
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <div className="flex items-center space-x-2">
                      <Clock className="h-4 w-4" />
                      <span>{new Date(item.timestamp).toLocaleDateString()} at {new Date(item.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div className="text-xs">
                      ID: {item.id}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Results Summary */}
        {filteredFeedback.length > 0 && (
          <div className="mt-8 text-center text-sm text-gray-600">
            Showing {filteredFeedback.length} of {feedback.length} feedback items
          </div>
        )}
      </div>
    </div>
  );
};

export default FeedbackView; 