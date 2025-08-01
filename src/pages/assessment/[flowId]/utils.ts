/**
 * Assessment Flow Page Utils
 * Server-side props and utility functions for assessment flow pages
 */

import type { GetServerSideProps } from 'next';

export const getServerSideProps: GetServerSideProps = async (context) => {
  return {
    props: {
      flowId: context.params?.flowId as string
    }
  };
};
