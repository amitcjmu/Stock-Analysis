import React from 'react'
import { useState } from 'react'
import { useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Checkbox } from '../ui/checkbox';
import { RadioGroup, RadioGroupItem } from '../ui/radio-group';
import { Progress } from '../ui/progress';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Info } from 'lucide-react'
import { Upload, FileText, CheckCircle, AlertCircle, Clock, ChevronRight, ChevronDown } from 'lucide-react'
import { useDropzone } from 'react-dropzone';
import { toast } from 'sonner';

export interface QuestionOption {
  value: string;
  label: string;
  description?: string;
}

export interface ValidationRule {
  type: 'min' | 'max' | 'pattern' | 'minLength' | 'maxLength' | 'custom';
  value?: string | number;
  message?: string;
  validator?: (value: string | number | boolean | string[] | File[]) => boolean | string;
}

export interface QualifyingQuestion {
  id: string;
  question: string;
  question_type: 'text' | 'select' | 'multiselect' | 'file_upload' | 'boolean' | 'numeric';
  category: string;
  priority: number;
  required: boolean;
  options?: QuestionOption[];
  validation_rules?: Record<string, ValidationRule>;
  help_text?: string;
  depends_on?: string;
}

export interface QuestionResponse {
  question_id: string;
  response: string | number | boolean | string[] | File[];
  confidence: number;
  source: string;
  timestamp: Date;
}

interface QualifyingQuestionsProps {
  questions: QualifyingQuestion[];
  responses: QuestionResponse[];
  onResponseChange: (questionId: string, response: string | number | boolean | string[] | File[]) => void;
  onSubmit: (responses: QuestionResponse[], isPartial?: boolean) => void;
  disabled?: boolean;
  showProgress?: boolean;
  className?: string;
}

interface FileUploadProps {
  questionId: string;
  onFileChange: (files: File[]) => void;
  accept?: string;
  maxFiles?: number;
  disabled?: boolean;
}

const FileUpload: React.FC<FileUploadProps> = ({
  questionId,
  onFileChange,
  accept = '.txt,.pdf,.doc,.docx,.java,.py,.js,.ts,.cs,.sql',
  maxFiles = 5,
  disabled = false
}) => {
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = [...uploadedFiles, ...acceptedFiles].slice(0, maxFiles);
    setUploadedFiles(newFiles);
    onFileChange(newFiles);
    toast.success(`${acceptedFiles.length} file(s) uploaded successfully`);
  }, [uploadedFiles, maxFiles, onFileChange]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: accept.split(',').reduce((acc, ext) => ({ ...acc, [ext]: [] }), {}),
    maxFiles,
    disabled
  });

  const removeFile = (index: number) => {
    const newFiles = uploadedFiles.filter((_, i) => i !== index);
    setUploadedFiles(newFiles);
    onFileChange(newFiles);
  };

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-8 w-8 text-gray-400 mb-2" />
        {isDragActive ? (
          <p className="text-blue-600">Drop the files here...</p>
        ) : (
          <div>
            <p className="text-gray-600">Drag & drop files here, or click to select</p>
            <p className="text-xs text-gray-500 mt-1">
              Supports: {accept} (max {maxFiles} files)
            </p>
          </div>
        )}
      </div>

      {uploadedFiles.length > 0 && (
        <div className="space-y-2">
          <Label className="text-sm font-medium">Uploaded Files:</Label>
          {uploadedFiles.map((file, index) => (
            <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
              <div className="flex items-center space-x-2">
                <FileText className="h-4 w-4 text-gray-500" />
                <span className="text-sm">{file.name}</span>
                <span className="text-xs text-gray-500">
                  ({(file.size / 1024).toFixed(1)} KB)
                </span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => removeFile(index)}
                disabled={disabled}
              >
                Remove
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export const QualifyingQuestions: React.FC<QualifyingQuestionsProps> = ({
  questions,
  responses,
  onResponseChange,
  onSubmit,
  disabled = false,
  showProgress = true,
  className = ''
}) => {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [currentTab, setCurrentTab] = useState<string>('all');

  // Group questions by category
  const questionsByCategory = questions.reduce((acc, question) => {
    if (!acc[question.category]) {
      acc[question.category] = [];
    }
    acc[question.category].push(question);
    return acc;
  }, {} as Record<string, QualifyingQuestion[]>);

  // Sort categories by priority (based on highest priority question in category)
  const sortedCategories = Object.keys(questionsByCategory).sort((a, b) => {
    const maxPriorityA = Math.max(...questionsByCategory[a].map(q => q.priority));
    const maxPriorityB = Math.max(...questionsByCategory[b].map(q => q.priority));
    return maxPriorityA - maxPriorityB;
  });

  // Calculate progress
  const totalQuestions = questions.length;
  const answeredQuestions = responses.length;
  const requiredQuestions = questions.filter(q => q.required).length;
  const answeredRequiredQuestions = responses.filter(r =>
    questions.find(q => q.id === r.question_id)?.required
  ).length;
  const progressPercentage = totalQuestions > 0 ? (answeredQuestions / totalQuestions) * 100 : 0;

  const getResponseValue = (questionId: string) => {
    const response = responses.find(r => r.question_id === questionId);
    return response?.response;
  };

  const handleResponseChange = (questionId: string, value: string | number | boolean | string[] | File[]) => {
    onResponseChange(questionId, value);
  };

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const renderQuestion = (question: QualifyingQuestion) => {
    const currentValue = getResponseValue(question.id);
    const isAnswered = currentValue !== undefined && currentValue !== null && currentValue !== '';

    return (
      <div key={question.id} className="space-y-4 p-4 border border-gray-200 rounded-lg">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <Label className="text-sm font-medium">
                {question.question}
                {question.required && <span className="text-red-500 ml-1">*</span>}
              </Label>
              {isAnswered && <CheckCircle className="h-4 w-4 text-green-500" />}
              {question.required && !isAnswered && (
                <AlertCircle className="h-4 w-4 text-orange-500" />
              )}
            </div>
            {question.help_text && (
              <p className="text-xs text-gray-500 mt-1">{question.help_text}</p>
            )}
          </div>
          <Badge variant={question.priority <= 2 ? 'default' : 'secondary'}>
            Priority {question.priority}
          </Badge>
        </div>

        <div className="space-y-2">
          {question.question_type === 'text' && (
            <Input
              value={currentValue as string || ''}
              onChange={(e) => handleResponseChange(question.id, e.target.value)}
              placeholder="Enter your response..."
              disabled={disabled}
            />
          )}

          {question.question_type === 'numeric' && (
            <Input
              type="number"
              value={currentValue as number || ''}
              onChange={(e) => handleResponseChange(question.id, parseFloat(e.target.value) || 0)}
              placeholder="Enter a number..."
              disabled={disabled}
            />
          )}

          {question.question_type === 'select' && question.options && (
            <Select
              value={currentValue as string || ''}
              onValueChange={(value) => handleResponseChange(question.id, value)}
              disabled={disabled}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select an option..." />
              </SelectTrigger>
              <SelectContent>
                {question.options.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    <div className="flex flex-col">
                      <span>{option.label}</span>
                      {option.description && (
                        <span className="text-xs text-gray-500">{option.description}</span>
                      )}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          {question.question_type === 'multiselect' && question.options && (
            <div className="space-y-2">
              {question.options.map((option) => (
                <div key={option.value} className="flex items-center space-x-2">
                  <Checkbox
                    id={`${question.id}-${option.value}`}
                    checked={(currentValue as string[] || []).includes(option.value)}
                    onCheckedChange={(checked) => {
                      const currentArray = (currentValue as string[]) || [];
                      const newArray = checked
                        ? [...currentArray, option.value]
                        : currentArray.filter(v => v !== option.value);
                      handleResponseChange(question.id, newArray);
                    }}
                    disabled={disabled}
                  />
                  <Label htmlFor={`${question.id}-${option.value}`} className="text-sm">
                    {option.label}
                    {option.description && (
                      <span className="text-xs text-gray-500 block">{option.description}</span>
                    )}
                  </Label>
                </div>
              ))}
            </div>
          )}

          {question.question_type === 'boolean' && (
            <RadioGroup
              value={currentValue?.toString() || ''}
              onValueChange={(value) => handleResponseChange(question.id, value === 'true')}
              disabled={disabled}
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="true" id={`${question.id}-yes`} />
                <Label htmlFor={`${question.id}-yes`}>Yes</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="false" id={`${question.id}-no`} />
                <Label htmlFor={`${question.id}-no`}>No</Label>
              </div>
            </RadioGroup>
          )}

          {question.question_type === 'file_upload' && (
            <FileUpload
              questionId={question.id}
              onFileChange={(files) => handleResponseChange(question.id, files)}
              disabled={disabled}
            />
          )}
        </div>
      </div>
    );
  };

  const renderCategorySection = (category: string) => {
    const categoryQuestions = questionsByCategory[category];
    const isExpanded = expandedCategories.has(category);
    const answeredInCategory = categoryQuestions.filter(q =>
      getResponseValue(q.id) !== undefined
    ).length;

    return (
      <div key={category} className="space-y-4">
        <div
          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100"
          onClick={() => toggleCategory(category)}
        >
          <div className="flex items-center space-x-3">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
            <h3 className="font-medium">{category}</h3>
            <Badge variant="outline">
              {answeredInCategory}/{categoryQuestions.length} answered
            </Badge>
          </div>
          <div className="flex items-center space-x-2">
            <Progress
              value={(answeredInCategory / categoryQuestions.length) * 100}
              className="w-20 h-2"
            />
          </div>
        </div>

        {isExpanded && (
          <div className="space-y-4 ml-4">
            {categoryQuestions.map(renderQuestion)}
          </div>
        )}
      </div>
    );
  };

  const canSubmit = answeredRequiredQuestions === requiredQuestions;

  return (
    <Card className={`w-full ${className}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg font-semibold">Qualifying Questions</CardTitle>
            <CardDescription>
              Answer these questions to refine your 6R analysis recommendations
            </CardDescription>
          </div>
          {showProgress && (
            <div className="text-right">
              <div className="text-sm text-gray-600">
                {answeredQuestions}/{totalQuestions} questions answered
              </div>
              <div className="text-xs text-gray-500">
                {answeredRequiredQuestions}/{requiredQuestions} required completed
              </div>
            </div>
          )}
        </div>

        {showProgress && (
          <div className="space-y-2">
            <Progress value={progressPercentage} className="w-full" />
            <div className="flex justify-between text-xs text-gray-500">
              <span>Progress: {Math.round(progressPercentage)}%</span>
              <span>
                {canSubmit ? (
                  <span className="text-green-600 flex items-center">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Ready to submit
                  </span>
                ) : (
                  <span className="text-orange-600 flex items-center">
                    <Clock className="h-3 w-3 mr-1" />
                    {requiredQuestions - answeredRequiredQuestions} required remaining
                  </span>
                )}
              </span>
            </div>
          </div>
        )}
      </CardHeader>

      <CardContent className="space-y-6">
        <Tabs value={currentTab} onValueChange={setCurrentTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="all">All Questions</TabsTrigger>
            <TabsTrigger value="required">Required Only</TabsTrigger>
            <TabsTrigger value="unanswered">Unanswered</TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="space-y-4">
            {sortedCategories.map(renderCategorySection)}
          </TabsContent>

          <TabsContent value="required" className="space-y-4">
            {sortedCategories
              .filter(category =>
                questionsByCategory[category].some(q => q.required)
              )
              .map(category => {
                const requiredQuestions = questionsByCategory[category].filter(q => q.required);
                return (
                  <div key={category} className="space-y-4">
                    <h3 className="font-medium text-gray-900">{category}</h3>
                    {requiredQuestions.map(renderQuestion)}
                  </div>
                );
              })}
          </TabsContent>

          <TabsContent value="unanswered" className="space-y-4">
            {sortedCategories
              .filter(category =>
                questionsByCategory[category].some(q =>
                  getResponseValue(q.id) === undefined
                )
              )
              .map(category => {
                const unansweredQuestions = questionsByCategory[category].filter(q =>
                  getResponseValue(q.id) === undefined
                );
                return (
                  <div key={category} className="space-y-4">
                    <h3 className="font-medium text-gray-900">{category}</h3>
                    {unansweredQuestions.map(renderQuestion)}
                  </div>
                );
              })}
          </TabsContent>
        </Tabs>

        <Separator />

        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-600">
            {answeredQuestions > 0 && (
              <span>
                Last updated: {new Date().toLocaleTimeString()}
              </span>
            )}
          </div>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              onClick={() => onSubmit(responses, true)}
              disabled={disabled || answeredQuestions === 0}
            >
              Save Progress
            </Button>
            <Button
              onClick={() => onSubmit(responses, false)}
              disabled={disabled || !canSubmit}
            >
              Submit Responses
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default QualifyingQuestions;
