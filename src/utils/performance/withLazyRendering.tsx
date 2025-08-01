import React, { useRef } from 'react';

/**
 * Higher-order component for lazy rendering
 */
const withLazyRendering = <P extends object>(
  Component: React.ComponentType<P>,
  options: {
    threshold?: number; // Intersection threshold
    rootMargin?: string;
    displayName?: string;
  } = {}
): React.FC<P> => {
  const { threshold = 0.1, rootMargin = '100px', displayName } = options;
  const componentName = displayName || Component.displayName || Component.name || 'Anonymous';

  const LazyComponent: React.FC<P> = (props) => {
    const [isVisible, setIsVisible] = React.useState(false);
    const [hasRendered, setHasRendered] = React.useState(false);
    const ref = useRef<HTMLDivElement>(null);

    React.useEffect(() => {
      const element = ref.current;
      if (!element) return;

      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting && !hasRendered) {
            setIsVisible(true);
            setHasRendered(true);
          }
        },
        { threshold, rootMargin }
      );

      observer.observe(element);

      return () => observer.disconnect();
    }, [hasRendered]);

    return (
      <div ref={ref}>
        {isVisible ? <Component {...props} /> : (
          <div className="h-32 flex items-center justify-center bg-gray-50">
            <div className="text-sm text-gray-500">Loading...</div>
          </div>
        )}
      </div>
    );
  };

  LazyComponent.displayName = `LazyRendering(${componentName})`;
  return LazyComponent;
};

export default withLazyRendering;