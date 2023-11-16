// components/Logo.tsx
import React from 'react';

const Logo: React.FC = () => {
  return (
    <div>
      {/* Your Tailwind CSS classes go here */}
      <img className="w-32 h-32" src="/E-Rex-circular.png" alt="Logo" />
    </div>
  );
};

export default Logo;