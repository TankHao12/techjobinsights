import React from 'react';
import { motion } from 'framer-motion';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  onClick?: () => void;
  gradient?: boolean;
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  className = '',
  hover = true,
  onClick,
  gradient = false
}) => {
  const cardClasses = `
    glass-card 
    ${hover ? 'glass-card-hover cursor-pointer' : ''}
    ${gradient ? 'ai-gradient-border' : ''}
    ${className}
  `;

  const cardVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    hover: hover ? { 
      y: -8, 
      scale: 1.02,
      transition: { duration: 0.3 }
    } : {},
  };

  return (
    <motion.div
      className={cardClasses}
      variants={cardVariants}
      initial="initial"
      animate="animate"
      whileHover="hover"
      onClick={onClick}
      layout
    >
      {gradient && (
        <div className="relative z-10 p-6">
          {children}
        </div>
      )}
      {!gradient && (
        <div className="p-6">
          {children}
        </div>
      )}
    </motion.div>
  );
};

export default GlassCard;