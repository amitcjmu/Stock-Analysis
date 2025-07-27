import React from 'react'
import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Shield, Mail, Lock, User, Building2, Eye, EyeOff, AlertCircle, CheckCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/AuthContext';

// Demo credentials that match the database seed
const DEMO_EMAIL = "demo@democorp.com";
const DEMO_PASSWORD = import.meta.env.VITE_DEMO_PASSWORD || ""; // Demo password from environment

const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, register } = useAuth();
  const { toast } = useToast();

  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [registrationSuccess, setRegistrationSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Login form state
  const [loginData, setLoginData] = useState({
    email: '',
    password: ''
  });

  // Registration form state
  const [registerData, setRegisterData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    username: '',
    organization: '',
    role_description: '',
    justification: '',
    requested_access: {
      client_accounts: [],
      engagements: [],
      access_level: 'read'
    }
  });

  const from = location.state?.from?.pathname || '/';

  const handleLogin = async (e: React.FormEvent): void => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await login(loginData.email, loginData.password);
      toast({
        title: "Login Successful",
        description: "Welcome to AI Modernize Migration Platform",
      });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent): void => {
    e.preventDefault();

    if (registerData.password !== registerData.confirmPassword) {
      toast({
        title: "Registration Failed",
        description: "Passwords do not match",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);

    try {
      await register({
        email: registerData.email,
        password: registerData.password,
        full_name: registerData.full_name,
        username: registerData.username,
        organization: registerData.organization,
        role_description: registerData.role_description,
        justification: registerData.justification,
        requested_access: registerData.requested_access
      });

      setRegistrationSuccess(true);
      toast({
        title: "Registration Submitted",
        description: "Your registration has been submitted for admin approval. You will receive an email when approved.",
      });
    } catch (error) {
      toast({
        title: "Registration Failed",
        description: (error as Error).message,
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  if (registrationSuccess) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-6">
        <Card className="max-w-md w-full">
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <CardTitle className="text-green-900">Registration Submitted</CardTitle>
            <CardDescription>
              Your account request has been submitted for administrative review.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <h4 className="font-medium text-green-900 mb-2">What happens next?</h4>
              <ul className="text-sm text-green-800 space-y-1">
                <li>• An administrator will review your request</li>
                <li>• You'll receive an email notification when approved</li>
                <li>• Approval typically takes 1-2 business days</li>
              </ul>
            </div>
            <div className="space-y-2">
              <Button
                onClick={() => setIsLogin(true)}
                variant="outline"
                className="w-full"
              >
                Back to Login
              </Button>
              <p className="text-xs text-center text-gray-600">
                Already have an approved account? Login above.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-6">
      <Card className="max-w-md w-full">
        <CardHeader className="text-center">
          <div className="mx-auto w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center mb-4">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <CardTitle className="text-gray-900">
            {isLogin ? 'Sign In' : 'Request Access'}
          </CardTitle>
          <CardDescription>
            {isLogin
              ? 'Access AI Modernize Migration Platform'
              : 'Request access to the migration platform'
            }
          </CardDescription>
        </CardHeader>

        <CardContent>
          {isLogin ? (
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="demo@democorp.com"
                    className="pl-10"
                    value={loginData.email}
                    onChange={(e) => setLoginData(prev => ({ ...prev, email: e.target.value }))}
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter your password"
                    className="pl-10 pr-10"
                    value={loginData.password}
                    onChange={(e) => setLoginData(prev => ({ ...prev, password: e.target.value }))}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="font-medium text-blue-900 text-sm mb-2">Demo Credentials:</h4>
                <div className="text-xs text-blue-800 space-y-1">
                  <div><strong>Demo User:</strong> demo@demo-corp.com / Demo123!</div>
                  <div><strong>Manager:</strong> manager@demo-corp.com / Demo123!</div>
                  <div><strong>Analyst:</strong> analyst@demo-corp.com / Demo123!</div>
                  <div><strong>Viewer:</strong> viewer@demo-corp.com / Demo123!</div>
                </div>
              </div>

              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Signing In...' : 'Sign In'}
              </Button>

              {error && (
                <div className="flex items-center text-red-600 text-sm mt-2">
                  <AlertCircle className="w-4 h-4 mr-1" />
                  <span>{error}</span>
                </div>
              )}
            </form>
          ) : (
            <form onSubmit={handleRegister} className="space-y-4">
              <div className="grid grid-cols-1 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="reg-full-name">Full Name *</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="reg-full-name"
                      placeholder="John Doe"
                      className="pl-10"
                      value={registerData.full_name}
                      onChange={(e) => setRegisterData(prev => ({ ...prev, full_name: e.target.value }))}
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="reg-email">Email *</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="reg-email"
                      type="email"
                      placeholder="john.doe@company.com"
                      className="pl-10"
                      value={registerData.email}
                      onChange={(e) => setRegisterData(prev => ({ ...prev, email: e.target.value }))}
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="reg-username">Username *</Label>
                  <Input
                    id="reg-username"
                    placeholder="john.doe"
                    value={registerData.username}
                    onChange={(e) => setRegisterData(prev => ({ ...prev, username: e.target.value }))}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="reg-organization">Organization *</Label>
                  <div className="relative">
                    <Building2 className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="reg-organization"
                      placeholder="TechCorp Solutions"
                      className="pl-10"
                      value={registerData.organization}
                      onChange={(e) => setRegisterData(prev => ({ ...prev, organization: e.target.value }))}
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="reg-role">Role Description *</Label>
                  <Input
                    id="reg-role"
                    placeholder="Senior Data Analyst"
                    value={registerData.role_description}
                    onChange={(e) => setRegisterData(prev => ({ ...prev, role_description: e.target.value }))}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="reg-password">Password *</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="reg-password"
                      type="password"
                      placeholder="Create a strong password"
                      className="pl-10"
                      value={registerData.password}
                      onChange={(e) => setRegisterData(prev => ({ ...prev, password: e.target.value }))}
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="reg-confirm-password">Confirm Password *</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="reg-confirm-password"
                      type="password"
                      placeholder="Confirm your password"
                      className="pl-10"
                      value={registerData.confirmPassword}
                      onChange={(e) => setRegisterData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="access-level">Requested Access Level</Label>
                  <Select
                    value={registerData.requested_access.access_level}
                    onValueChange={(value) =>
                      setRegisterData(prev => ({
                        ...prev,
                        requested_access: { ...prev.requested_access, access_level: value }
                      }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select access level" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="read">Read Only</SelectItem>
                      <SelectItem value="read_write">Read & Write</SelectItem>
                      <SelectItem value="admin">Administrator</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="justification">Access Justification *</Label>
                  <Textarea
                    id="justification"
                    placeholder="Please explain why you need access to the platform and your role in migration projects..."
                    className="min-h-20"
                    value={registerData.justification}
                    onChange={(e) => setRegisterData(prev => ({ ...prev, justification: e.target.value }))}
                    required
                  />
                </div>
              </div>

              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5" />
                  <div>
                    <p className="text-sm text-muted-foreground">
                      Demo: {DEMO_EMAIL} / {DEMO_PASSWORD}
                    </p>
                    <p><strong>Access Review Process:</strong></p>
                    <p>Your request will be reviewed by an administrator. Approval typically takes 1-2 business days.</p>
                  </div>
                </div>
              </div>

              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Submitting Request...' : 'Submit Access Request'}
              </Button>
            </form>
          )}

          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={() => setIsLogin(!isLogin)}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              {isLogin
                ? "Need access? Request an account"
                : "Already have an account? Sign in"
              }
            </button>
          </div>

          {isLogin && (
            <div className="mt-4 text-center">
              <Link
                to="/"
                className="text-xs text-gray-500 hover:text-gray-700"
              >
                Back to Platform
              </Link>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Login;
