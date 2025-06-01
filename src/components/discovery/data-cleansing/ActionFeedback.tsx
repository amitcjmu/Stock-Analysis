import React from 'react';
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react';

export interface ActionFeedback {
  type: 'success' | 'error' | 'info';
  message: string;
  details?: string;
}

interface ActionFeedbackProps {
  feedback: ActionFeedback;
}

const ActionFeedback: React.FC<ActionFeedbackProps> = ({ feedback }) => {
  return (
    <div className={`mb-6 p-4 rounded-lg border ${
      feedback.type === 'success' ? 'bg-green-50 border-green-200' :
      feedback.type === 'error' ? 'bg-red-50 border-red-200' :
      'bg-blue-50 border-blue-200'
    }`}>
      <div className="flex items-start space-x-3">
        {feedback.type === 'success' && <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />}
        {feedback.type === 'error' && <XCircle className="h-5 w-5 text-red-600 mt-0.5" />}
        {feedback.type === 'info' && <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />}
        <div>
          <p className={`font-medium ${
            feedback.type === 'success' ? 'text-green-800' :
            feedback.type === 'error' ? 'text-red-800' :
            'text-blue-800'
          }`}>
            {feedback.message}
          </p>
          {feedback.details && (
            <p className={`text-sm mt-1 ${
              feedback.type === 'success' ? 'text-green-600' :
              feedback.type === 'error' ? 'text-red-600' :
              'text-blue-600'
            }`}>
              {feedback.details}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ActionFeedback; 