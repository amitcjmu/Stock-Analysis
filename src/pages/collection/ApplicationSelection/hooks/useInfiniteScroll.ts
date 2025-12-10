/**
 * useInfiniteScroll Hook
 * Manages intersection observer for infinite scroll functionality
 *
 * CRITICAL: Preserves intersection observer pattern for smooth UX
 *
 * Bug Fix: The observer root must be the scrollable container, not the viewport,
 * when the list is inside an overflow container. Otherwise the loadMoreRef
 * element will never intersect because it's constrained within the container.
 */

import { useEffect, useRef } from "react";

interface UseInfiniteScrollProps {
  hasNextPage: boolean;
  isFetchingNextPage: boolean;
  fetchNextPage: () => void;
}

interface UseInfiniteScrollReturn {
  loadMoreRef: React.RefObject<HTMLDivElement>;
  scrollContainerRef: React.RefObject<HTMLDivElement>;
}

/**
 * Hook for managing infinite scroll with Intersection Observer
 * Returns both a loadMoreRef (trigger element) and scrollContainerRef (scrollable container)
 */
export const useInfiniteScroll = ({
  hasNextPage,
  isFetchingNextPage,
  fetchNextPage,
}: UseInfiniteScrollProps): UseInfiniteScrollReturn => {
  const loadMoreRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  // Setup intersection observer for infinite scroll
  useEffect(() => {
    if (!loadMoreRef.current || !hasNextPage || isFetchingNextPage) return;

    // Use the scroll container as root if available, otherwise use viewport
    const rootElement = scrollContainerRef.current || null;

    observerRef.current = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry.isIntersecting && hasNextPage && !isFetchingNextPage) {
          console.log("📄 Loading next page of assets...");
          fetchNextPage();
        }
      },
      {
        root: rootElement,
        threshold: 0.1,
        rootMargin: "100px",
      },
    );

    observerRef.current.observe(loadMoreRef.current);

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [fetchNextPage, hasNextPage, isFetchingNextPage]);

  return {
    loadMoreRef,
    scrollContainerRef,
  };
};
