import React from 'react'
import { useState, useEffect, useCallback } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Shield, Mail, Lock, User, Building2, Eye, EyeOff, AlertCircle, CheckCircle, XCircle, Info } from 'lucide-react';
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
  const { login, register, error: authError } = useAuth();
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
      access_level: 'read_only'
    }
  });

  // Validation errors state
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [touchedFields, setTouchedFields] = useState<Set<string>>(new Set());
  const [isFormValid, setIsFormValid] = useState(false);

  const from = location.state?.from?.pathname || '/';

  // Validation rules
  const validateEmail = (email: string): string => {
    if (!email) return 'Email is required';
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailRegex.test(email)) return 'Please enter a valid email address';
    return '';
  };

  const validatePassword = (password: string): string => {
    if (!password) return 'Password is required';
    if (password.length < 8) return 'Password must be at least 8 characters long';
    if (!/[A-Z]/.test(password)) return 'Password must contain at least one uppercase letter';
    if (!/[a-z]/.test(password)) return 'Password must contain at least one lowercase letter';
    if (!/[0-9]/.test(password)) return 'Password must contain at least one number';
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) return 'Password must contain at least one special character';
    return '';
  };

  const validateConfirmPassword = (confirmPassword: string, password: string): string => {
    if (!confirmPassword) return 'Please confirm your password';
    if (confirmPassword !== password) return 'Passwords do not match';
    return '';
  };

  const validateFullName = (name: string): string => {
    if (!name) return 'Full name is required';
    if (name.length < 2) return 'Full name must be at least 2 characters long';
    if (!/^[a-zA-Z\s'-]+$/.test(name)) return 'Full name can only contain letters, spaces, hyphens, and apostrophes';
    return '';
  };

  const validateUsername = (username: string): string => {
    if (!username) return 'Username is required';
    if (username.length < 3) return 'Username must be at least 3 characters long';
    if (username.length > 20) return 'Username must be less than 20 characters';
    if (!/^[a-zA-Z0-9._-]+$/.test(username)) return 'Username can only contain letters, numbers, dots, underscores, and hyphens';
    if (/^[._-]/.test(username) || /[._-]$/.test(username)) return 'Username cannot start or end with special characters';
    return '';
  };

  const validateOrganization = (org: string): string => {
    if (!org) return 'Organization is required';
    if (org.length < 2) return 'Organization name must be at least 2 characters long';
    return '';
  };

  const validateRoleDescription = (role: string): string => {
    if (!role) return 'Role description is required';
    if (role.length < 2) return 'Role description must be at least 2 characters long';
    return '';
  };

  const validateJustification = (justification: string): string => {
    if (!justification) return 'Access justification is required';
    if (justification.length < 20) return 'Please provide at least 20 characters explaining why you need access';
    if (justification.length > 500) return 'Justification must be less than 500 characters';
    return '';
  };

  // Validate single field
  const validateField = useCallback((fieldName: string, value: string): string => {
    switch (fieldName) {
      case 'email':
        return validateEmail(value);
      case 'password':
        return validatePassword(value);
      case 'confirmPassword':
        return validateConfirmPassword(value, registerData.password);
      case 'full_name':
        return validateFullName(value);
      case 'username':
        return validateUsername(value);
      case 'organization':
        return validateOrganization(value);
      case 'role_description':
        return validateRoleDescription(value);
      case 'justification':
        return validateJustification(value);
      default:
        return '';
    }
  }, [registerData.password]);

  // Validate entire form
  const validateForm = useCallback((): boolean => {
    const errors: Record<string, string> = {};

    errors.email = validateEmail(registerData.email);
    errors.password = validatePassword(registerData.password);
    errors.confirmPassword = validateConfirmPassword(registerData.confirmPassword, registerData.password);
    errors.full_name = validateFullName(registerData.full_name);
    errors.username = validateUsername(registerData.username);
    errors.organization = validateOrganization(registerData.organization);
    errors.role_description = validateRoleDescription(registerData.role_description);
    errors.justification = validateJustification(registerData.justification);

    // Remove empty errors
    Object.keys(errors).forEach(key => {
      if (!errors[key]) delete errors[key];
    });

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  }, [registerData]);

  // Update form validity whenever registerData changes
  useEffect(() => {
    if (!isLogin) {
      const isValid = validateForm();
      setIsFormValid(isValid);
    }
  }, [registerData, validateForm, isLogin]);

  // Handle field change with validation
  const handleFieldChange = (fieldName: string, value: string) => {
    // Update the field value
    if (fieldName === 'access_level') {
      setRegisterData(prev => ({
        ...prev,
        requested_access: { ...prev.requested_access, access_level: value }
      }));
    } else {
      setRegisterData(prev => ({ ...prev, [fieldName]: value }));
    }

    // Mark field as touched
    setTouchedFields(prev => new Set(prev).add(fieldName));

    // Validate the field
    const error = validateField(fieldName, value);
    setValidationErrors(prev => {
      const newErrors = { ...prev };
      if (error) {
        newErrors[fieldName] = error;
      } else {
        delete newErrors[fieldName];
      }

      // Also validate confirmPassword when password changes
      if (fieldName === 'password' && registerData.confirmPassword) {
        const confirmError = validateConfirmPassword(registerData.confirmPassword, value);
        if (confirmError) {
          newErrors.confirmPassword = confirmError;
        } else {
          delete newErrors.confirmPassword;
        }
      }

      return newErrors;
    });
  };

  // Handle field blur
  const handleFieldBlur = (fieldName: string) => {
    setTouchedFields(prev => new Set(prev).add(fieldName));
    const value = fieldName === 'access_level'
      ? registerData.requested_access.access_level
      : (registerData[fieldName as keyof typeof registerData] as string);
    const error = validateField(fieldName, value);
    if (error) {
      setValidationErrors(prev => ({ ...prev, [fieldName]: error }));
    }
  };

  // Helper to get field error
  const getFieldError = (fieldName: string): string | undefined => {
    return touchedFields.has(fieldName) ? validationErrors[fieldName] : undefined;
  };

  // Helper to get field validation state
  const getFieldState = (fieldName: string): 'error' | 'success' | 'default' => {
    if (!touchedFields.has(fieldName)) return 'default';
    return validationErrors[fieldName] ? 'error' : 'success';
  };

  const handleLogin = async (e: React.FormEvent): void => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await login(loginData.email, loginData.password);
      toast({
        title: "Login Successful",
        description: "Welcome to AI Force Assess",
      });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent): void => {
    e.preventDefault();

    // Mark all fields as touched to show validation errors
    const allFields = ['email', 'password', 'confirmPassword', 'full_name', 'username', 'organization', 'role_description', 'justification'];
    setTouchedFields(new Set(allFields));

    // Validate the form
    if (!validateForm()) {
      toast({
        title: "Validation Failed",
        description: "Please fix all errors before submitting",
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
        username: registerData.username || undefined,
        organization: registerData.organization,
        role_description: registerData.role_description,
        registration_reason: registerData.justification, // Backend expects registration_reason
        requested_access_level: registerData.requested_access.access_level // Backend expects flat field, not nested object
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
          <h1 className="text-2xl font-bold text-blue-600 mb-2">AI Force Assess</h1>
          <CardTitle className="text-gray-900">
            {isLogin ? 'Sign In' : 'Request Access'}
          </CardTitle>
          <CardDescription>
            {isLogin
              ? 'Cloud Migration Assessment Platform'
              : 'Request access to AI Force Assess'
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

              {error && (
                <div className="flex items-center p-3 bg-red-50 border border-red-200 rounded-lg text-red-600">
                  <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0" />
                  <span className="text-sm">{error}</span>
                </div>
              )}

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
                      className={`pl-10 pr-10 ${getFieldState('full_name') === 'error' ? 'border-red-500' : getFieldState('full_name') === 'success' ? 'border-green-500' : ''}`}
                      value={registerData.full_name}
                      onChange={(e) => handleFieldChange('full_name', e.target.value)}
                      onBlur={() => handleFieldBlur('full_name')}
                      aria-invalid={getFieldState('full_name') === 'error'}
                      aria-describedby="full-name-error"
                    />
                    {getFieldState('full_name') === 'success' && (
                      <CheckCircle className="absolute right-3 top-3 h-4 w-4 text-green-500" />
                    )}
                    {getFieldState('full_name') === 'error' && (
                      <XCircle className="absolute right-3 top-3 h-4 w-4 text-red-500" />
                    )}
                  </div>
                  {getFieldError('full_name') && (
                    <p id="full-name-error" className="text-sm text-red-600 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      {getFieldError('full_name')}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="reg-email">Email *</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="reg-email"
                      type="email"
                      placeholder="john.doe@company.com"
                      className={`pl-10 pr-10 ${getFieldState('email') === 'error' ? 'border-red-500' : getFieldState('email') === 'success' ? 'border-green-500' : ''}`}
                      value={registerData.email}
                      onChange={(e) => handleFieldChange('email', e.target.value)}
                      onBlur={() => handleFieldBlur('email')}
                      aria-invalid={getFieldState('email') === 'error'}
                      aria-describedby="email-error"
                    />
                    {getFieldState('email') === 'success' && (
                      <CheckCircle className="absolute right-3 top-3 h-4 w-4 text-green-500" />
                    )}
                    {getFieldState('email') === 'error' && (
                      <XCircle className="absolute right-3 top-3 h-4 w-4 text-red-500" />
                    )}
                  </div>
                  {getFieldError('email') && (
                    <p id="email-error" className="text-sm text-red-600 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      {getFieldError('email')}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="reg-username">Username *</Label>
                  <div className="relative">
                    <Input
                      id="reg-username"
                      placeholder="john.doe"
                      className={`pr-10 ${getFieldState('username') === 'error' ? 'border-red-500' : getFieldState('username') === 'success' ? 'border-green-500' : ''}`}
                      value={registerData.username}
                      onChange={(e) => handleFieldChange('username', e.target.value)}
                      onBlur={() => handleFieldBlur('username')}
                      aria-invalid={getFieldState('username') === 'error'}
                      aria-describedby="username-error"
                    />
                    {getFieldState('username') === 'success' && (
                      <CheckCircle className="absolute right-3 top-3 h-4 w-4 text-green-500" />
                    )}
                    {getFieldState('username') === 'error' && (
                      <XCircle className="absolute right-3 top-3 h-4 w-4 text-red-500" />
                    )}
                  </div>
                  {getFieldError('username') && (
                    <p id="username-error" className="text-sm text-red-600 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      {getFieldError('username')}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="reg-organization">Organization *</Label>
                  <div className="relative">
                    <Building2 className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="reg-organization"
                      placeholder="TechCorp Solutions"
                      className={`pl-10 pr-10 ${getFieldState('organization') === 'error' ? 'border-red-500' : getFieldState('organization') === 'success' ? 'border-green-500' : ''}`}
                      value={registerData.organization}
                      onChange={(e) => handleFieldChange('organization', e.target.value)}
                      onBlur={() => handleFieldBlur('organization')}
                      aria-invalid={getFieldState('organization') === 'error'}
                      aria-describedby="organization-error"
                    />
                    {getFieldState('organization') === 'success' && (
                      <CheckCircle className="absolute right-3 top-3 h-4 w-4 text-green-500" />
                    )}
                    {getFieldState('organization') === 'error' && (
                      <XCircle className="absolute right-3 top-3 h-4 w-4 text-red-500" />
                    )}
                  </div>
                  {getFieldError('organization') && (
                    <p id="organization-error" className="text-sm text-red-600 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      {getFieldError('organization')}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="reg-role">Role Description *</Label>
                  <div className="relative">
                    <Input
                      id="reg-role"
                      placeholder="Senior Data Analyst"
                      className={`pr-10 ${getFieldState('role_description') === 'error' ? 'border-red-500' : getFieldState('role_description') === 'success' ? 'border-green-500' : ''}`}
                      value={registerData.role_description}
                      onChange={(e) => handleFieldChange('role_description', e.target.value)}
                      onBlur={() => handleFieldBlur('role_description')}
                      aria-invalid={getFieldState('role_description') === 'error'}
                      aria-describedby="role-error"
                    />
                    {getFieldState('role_description') === 'success' && (
                      <CheckCircle className="absolute right-3 top-3 h-4 w-4 text-green-500" />
                    )}
                    {getFieldState('role_description') === 'error' && (
                      <XCircle className="absolute right-3 top-3 h-4 w-4 text-red-500" />
                    )}
                  </div>
                  {getFieldError('role_description') && (
                    <p id="role-error" className="text-sm text-red-600 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      {getFieldError('role_description')}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="reg-password">Password *</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="reg-password"
                      type="password"
                      placeholder="Create a strong password"
                      className={`pl-10 pr-10 ${getFieldState('password') === 'error' ? 'border-red-500' : getFieldState('password') === 'success' ? 'border-green-500' : ''}`}
                      value={registerData.password}
                      onChange={(e) => handleFieldChange('password', e.target.value)}
                      onBlur={() => handleFieldBlur('password')}
                      aria-invalid={getFieldState('password') === 'error'}
                      aria-describedby="password-error"
                    />
                    {getFieldState('password') === 'success' && (
                      <CheckCircle className="absolute right-3 top-3 h-4 w-4 text-green-500" />
                    )}
                    {getFieldState('password') === 'error' && (
                      <XCircle className="absolute right-3 top-3 h-4 w-4 text-red-500" />
                    )}
                  </div>
                  {getFieldError('password') && (
                    <p id="password-error" className="text-sm text-red-600 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      {getFieldError('password')}
                    </p>
                  )}
                  {!getFieldError('password') && registerData.password && (
                    <p className="text-xs text-gray-500 flex items-center gap-1">
                      <Info className="h-3 w-3" />
                      Must be 8+ characters with uppercase, lowercase, number, and special character
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="reg-confirm-password">Confirm Password *</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="reg-confirm-password"
                      type="password"
                      placeholder="Confirm your password"
                      className={`pl-10 pr-10 ${getFieldState('confirmPassword') === 'error' ? 'border-red-500' : getFieldState('confirmPassword') === 'success' ? 'border-green-500' : ''}`}
                      value={registerData.confirmPassword}
                      onChange={(e) => handleFieldChange('confirmPassword', e.target.value)}
                      onBlur={() => handleFieldBlur('confirmPassword')}
                      aria-invalid={getFieldState('confirmPassword') === 'error'}
                      aria-describedby="confirm-password-error"
                    />
                    {getFieldState('confirmPassword') === 'success' && (
                      <CheckCircle className="absolute right-3 top-3 h-4 w-4 text-green-500" />
                    )}
                    {getFieldState('confirmPassword') === 'error' && (
                      <XCircle className="absolute right-3 top-3 h-4 w-4 text-red-500" />
                    )}
                  </div>
                  {getFieldError('confirmPassword') && (
                    <p id="confirm-password-error" className="text-sm text-red-600 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      {getFieldError('confirmPassword')}
                    </p>
                  )}
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
                      <SelectItem value="read_only">Read Only</SelectItem>
                      <SelectItem value="read_write">Read & Write</SelectItem>
                      <SelectItem value="admin">Administrator</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="justification">Access Justification *</Label>
                  <div className="relative">
                    <Textarea
                      id="justification"
                      placeholder="Please explain why you need access to the platform and your role in migration projects..."
                      className={`min-h-20 ${getFieldState('justification') === 'error' ? 'border-red-500' : getFieldState('justification') === 'success' ? 'border-green-500' : ''}`}
                      value={registerData.justification}
                      onChange={(e) => handleFieldChange('justification', e.target.value)}
                      onBlur={() => handleFieldBlur('justification')}
                      aria-invalid={getFieldState('justification') === 'error'}
                      aria-describedby="justification-error"
                    />
                  </div>
                  <div className="flex justify-between items-center">
                    {getFieldError('justification') ? (
                      <p id="justification-error" className="text-sm text-red-600 flex items-center gap-1">
                        <AlertCircle className="h-3 w-3" />
                        {getFieldError('justification')}
                      </p>
                    ) : (
                      <p className="text-xs text-gray-500">
                        {registerData.justification.length}/500 characters
                      </p>
                    )}
                    {getFieldState('justification') === 'success' && (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    )}
                  </div>
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

              {/* Form validation status summary */}
              {!isLogin && touchedFields.size > 0 && Object.keys(validationErrors).length > 0 && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-start gap-2">
                    <XCircle className="w-4 h-4 text-red-600 mt-0.5" />
                    <div className="text-sm text-red-800">
                      <p className="font-medium mb-1">Please fix the following errors:</p>
                      <ul className="list-disc list-inside space-y-0.5">
                        {Object.entries(validationErrors).map(([field, error]) => (
                          touchedFields.has(field) && <li key={field}>{error}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {/* Success message when form is valid */}
              {!isLogin && isFormValid && touchedFields.size > 0 && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    <p className="text-sm text-green-800 font-medium">
                      All fields are valid. You can submit your request!
                    </p>
                  </div>
                </div>
              )}

              <Button
                type="submit"
                className="w-full"
                disabled={loading || (!isLogin && !isFormValid)}
              >
                {loading ? 'Submitting Request...' : (
                  !isFormValid && !isLogin ? 'Complete All Required Fields' : 'Submit Access Request'
                )}
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
