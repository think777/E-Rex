// components/Row.tsx
import React from 'react';

interface RowProps {
  data: { title: string; description: string };
}

const Row: React.FC<RowProps> = ({ data }) => {
  return (
    <div>
      {/* Your Tailwind CSS and TypeScript usage go here */}
      <p className="text-lg font-bold">{data.title}: {data.description}</p>
    </div>
  );
};

export default Row;