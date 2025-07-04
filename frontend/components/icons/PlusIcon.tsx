
import React from 'react';

interface PlusIconProps extends React.SVGProps<SVGSVGElement> {}

const PlusIcon: React.FC<PlusIconProps> = (props) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    width="20" 
    height="20" 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    {...props}
  >
    <path d="M5 12h14"/>
    <path d="M12 5v14"/>
  </svg>
);

export default PlusIcon;
