/**
 * ESLint Configuration for Field Naming Convention
 *
 * This configuration helps prevent the snake_case/camelCase confusion
 * that causes recurring bugs in the codebase.
 *
 * Add this to your main .eslintrc.js:
 * extends: ['./.eslintrc.field-naming.js']
 */

module.exports = {
  rules: {
    // Warn when accessing both snake_case and camelCase variants
    'no-restricted-syntax': [
      'warn',
      {
        selector: 'MemberExpression[property.name="flowId"][object.property.name="flow_id"]',
        message: 'Do not access both flow.flowId and flow.flow_id - use the transformer utility instead'
      },
      {
        selector: 'MemberExpression[property.name="flow_id"][object.property.name="flowId"]',
        message: 'Do not access both flow.flow_id and flow.flowId - use the transformer utility instead'
      }
    ],

    // Custom rule to enforce consistent field naming in interfaces
    '@typescript-eslint/naming-convention': [
      'warn',
      {
        selector: 'typeProperty',
        filter: {
          regex: '_id$|_at$|_by$|_name$|_type$|_status$',
          match: true
        },
        format: null,
        custom: {
          regex: '^[a-z]+(_[a-z]+)*$',
          match: true
        },
        leadingUnderscore: 'forbid',
        trailingUnderscore: 'forbid',
        prefix: [],
        suffix: [],
        // Add a comment to indicate this should be transformed
        // when used in frontend code
        message: 'Backend response fields should use snake_case. Remember to transform to camelCase for frontend use.'
      }
    ]
  },

  overrides: [
    {
      // For API response type definitions
      files: ['**/types/api/**/*.ts', '**/services/**/*.ts'],
      rules: {
        '@typescript-eslint/naming-convention': [
          'error',
          {
            selector: 'typeProperty',
            format: ['snake_case'],
            filter: {
              regex: '^(flow_id|client_account_id|engagement_id|.*_at|.*_by|.*_type|.*_status)$',
              match: true
            },
            message: 'API response types must use snake_case for backend fields'
          }
        ]
      }
    },
    {
      // For React component props and frontend types
      files: ['**/components/**/*.tsx', '**/hooks/**/*.ts', '**/pages/**/*.tsx'],
      rules: {
        '@typescript-eslint/naming-convention': [
          'error',
          {
            selector: 'typeProperty',
            format: ['camelCase'],
            filter: {
              regex: '^(flowId|clientAccountId|engagementId|.*At|.*By|.*Type|.*Status)$',
              match: true
            },
            message: 'Frontend types must use camelCase. Use the transformer utility for API responses.'
          }
        ]
      }
    }
  ]
};
