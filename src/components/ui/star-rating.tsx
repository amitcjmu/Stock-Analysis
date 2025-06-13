import React from 'react';
import { Star, StarHalf } from 'lucide-react';

interface StarRatingProps {
  value: number;
  onChange: (value: number) => void;
  size?: number;
}

export const StarRating: React.FC<StarRatingProps> = ({
  value,
  onChange,
  size = 24
}) => {
  const stars = [1, 2, 3, 4, 5];

  return (
    <div className="flex gap-1">
      {stars.map((star) => (
        <button
          key={star}
          type="button"
          onClick={() => onChange(star)}
          className={`text-${star <= value ? 'yellow' : 'gray'}-400 hover:text-yellow-400 transition-colors`}
        >
          <Star size={size} />
        </button>
      ))}
    </div>
  );
};
 