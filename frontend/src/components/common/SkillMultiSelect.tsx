import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { X, Check, AlertCircle } from 'lucide-react';
import { searchSkills } from '../../services/skillsService';

interface Props {
  selectedSkills: string[];
  onChange: (skills: string[]) => void;
  placeholder?: string;
  showAddButton?: boolean;
}

export const SkillMultiSelect: React.FC<Props> = ({ 
  selectedSkills, 
  onChange, 
  placeholder,
  showAddButton = true
}) => {
  const [input, setInput] = useState('');
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [hasSearched, setHasSearched] = useState(false);
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0, width: 0 });
  const wrapperRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Update dropdown position
  const updateDropdownPosition = () => {
    if (inputRef.current) {
      const rect = inputRef.current.getBoundingClientRect();
      setDropdownPosition({
        top: rect.bottom + window.scrollY,
        left: rect.left + window.scrollX,
        width: rect.width
      });
    }
  };

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      // Check if click is outside both the input wrapper AND the dropdown
      if (
        wrapperRef.current && 
        !wrapperRef.current.contains(target) &&
        dropdownRef.current &&
        !dropdownRef.current.contains(target)
      ) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Update position when showing suggestions
  useEffect(() => {
    if (showSuggestions) {
      updateDropdownPosition();
      
      // Update on scroll and resize
      window.addEventListener('scroll', updateDropdownPosition, true);
      window.addEventListener('resize', updateDropdownPosition);
      
      return () => {
        window.removeEventListener('scroll', updateDropdownPosition, true);
        window.removeEventListener('resize', updateDropdownPosition);
      };
    }
  }, [showSuggestions]);

  // Search for skills as user types
  useEffect(() => {
    const searchTimeout = setTimeout(async () => {
      if (input.length >= 2) {
        setIsSearching(true);
        setHasSearched(false);
        try {
          const results = await searchSkills(input, undefined, 10);
          setSuggestions(results);
          setShowSuggestions(true);
          setSelectedIndex(-1);
          setHasSearched(true);
        } catch (error) {
          console.error('Search failed:', error);
          setSuggestions([]);
          setHasSearched(true);
        } finally {
          setIsSearching(false);
        }
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
        setHasSearched(false);
      }
    }, 300);

    return () => clearTimeout(searchTimeout);
  }, [input]);

  const handleAdd = (skillName?: string) => {
    const skillToAdd = skillName || input.trim();
    if (skillToAdd && !selectedSkills.includes(skillToAdd)) {
      onChange([...selectedSkills, skillToAdd]);
      setInput('');
      setSuggestions([]);
      setShowSuggestions(false);
      setHasSearched(false);
    }
  };

  const handleRemove = (skill: string) => {
    onChange(selectedSkills.filter(s => s !== skill));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedIndex >= 0 && suggestions[selectedIndex]) {
        // Always allow adding from valid suggestions
        handleAdd(suggestions[selectedIndex].name);
      } else if (input.trim() && showAddButton) {
        // Only allow adding arbitrary text if Add button is shown
        handleAdd();
      }
      // If showAddButton is false and no suggestion selected, do nothing (prevent invalid skills)
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => 
        prev < suggestions.length - 1 ? prev + 1 : prev
      );
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  // Render dropdown in portal
  const renderDropdown = () => {
    if (!showSuggestions) return null;

    const dropdownContent = (
      <div ref={dropdownRef}>
        {/* Autocomplete Dropdown */}
        {suggestions.length > 0 && (
          <div 
            style={{
              position: 'fixed',
              top: `${dropdownPosition.top}px`,
              left: `${dropdownPosition.left}px`,
              width: `${dropdownPosition.width}px`,
              zIndex: 99999
            }}
            className="mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-2xl max-h-60 overflow-y-auto"
          >
            {suggestions.map((skill, index) => (
              <button
                key={skill.id}
                type="button"
                onClick={() => handleAdd(skill.name)}
                className={`w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center justify-between ${
                  index === selectedIndex ? 'bg-gray-100 dark:bg-gray-700' : ''
                } ${selectedSkills.includes(skill.name) ? 'opacity-50' : ''}`}
                disabled={selectedSkills.includes(skill.name)}
              >
                <div className="flex-1">
                  <div className="font-medium text-gray-900 dark:text-gray-100 capitalize">
                    {skill.name}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {skill.category?.replace(/_/g, ' ')} • {skill.job_count} jobs
                  </div>
                </div>
                {selectedSkills.includes(skill.name) && (
                  <Check className="w-4 h-4 text-green-600" />
                )}
              </button>
            ))}
          </div>
        )}

        {/* No results message */}
        {!isSearching && input.length >= 2 && suggestions.length === 0 && (
          <div 
            style={{
              position: 'fixed',
              top: `${dropdownPosition.top}px`,
              left: `${dropdownPosition.left}px`,
              width: `${dropdownPosition.width}px`,
              zIndex: 99999
            }}
            className="mt-1 bg-white dark:bg-gray-800 border border-amber-300 dark:border-amber-600 rounded-lg shadow-2xl p-4"
          >
            <div className="flex items-start gap-2 text-amber-600 dark:text-amber-400">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium mb-1">No matching skills found</p>
                <p className="text-xs text-amber-700 dark:text-amber-300">
                  {showAddButton 
                    ? "Please check spelling or try a different skill name."
                    : "This skill is not in our database. Please try a different search term or check your spelling."}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    );

    return createPortal(dropdownContent, document.body);
  };

  return (
    <div ref={wrapperRef} className="relative">
      <div className={showAddButton ? "flex gap-2 mb-2" : "mb-2"}>
        <div className="flex-1 relative">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={updateDropdownPosition}
            placeholder={placeholder}
            className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-600 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        {showAddButton && (
          <button 
            type="button"
            onClick={() => handleAdd()} 
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            disabled={!input.trim() || (hasSearched && suggestions.length === 0) || isSearching}
            title={hasSearched && suggestions.length === 0 ? "No matching skills found. Please select from suggestions." : "Add skill"}
          >
            Add
          </button>
        )}
      </div>

      {/* Render dropdown via portal */}
      {renderDropdown()}
      
      {/* Selected Skills Tags */}
      {selectedSkills.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {selectedSkills.map(skill => (
            <span 
              key={skill} 
              className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full flex items-center gap-2"
            >
              {skill}
              <X 
                className="w-4 h-4 cursor-pointer hover:text-red-600" 
                onClick={() => handleRemove(skill)} 
              />
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
