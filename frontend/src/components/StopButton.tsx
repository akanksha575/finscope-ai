import React from 'react';

interface StopButtonProps {
  onClick: () => void;
  title?: string;
  className?: string;
}

export const StopButton: React.FC<StopButtonProps> = ({ onClick, title = 'Stop', className = '' }) => (
  <button
    type="button"
    onClick={onClick}
    title={title}
    className={`p-1.5 rounded-full bg-white hover:bg-gray-100 flex items-center justify-center ${className}`}
  >
    {/* Dark square */}
    <div className="w-2 h-2 bg-gray-800" />
  </button>
);
