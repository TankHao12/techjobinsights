import React, { useState, useEffect, useRef } from 'react';
import { X, Check, AlertCircle } from 'lucide-react';
import { searchSkills } from '../../services/skillsService';

interface Props {
  selectedSkills: string[];
  onChange: (skills: string[]) => void;
  placeholder?: string;
}

export const SkillMultiSelect: React.FC<Props> = ({ 
  selectedSkills, 
  onChange, 
  placeholder 
}) => {
  const [input, setInput] = useState('');
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [hasSearched, setHasSearched] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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
        handleAdd(suggestions[selectedIndex].name);
      } else if (input.trim()) {
        handleAdd();
      }
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

  return (
    <div ref={wrapperRef} className="relative">
      <div className="flex gap-2 mb-2">
        <div className="flex-1 relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="w-full px-3 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-600 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          
          {/* Autocomplete Dropdown */}
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg max-h-60 overflow-y-auto">
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
          {showSuggestions && !isSearching && input.length >= 2 && suggestions.length === 0 && (
            <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-amber-300 dark:border-amber-600 rounded-lg shadow-lg p-4">
              <div className="flex items-start gap-2 text-amber-600 dark:text-amber-400">
                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium mb-1">No skills found in database</p>
                  <p className="text-xs text-amber-700 dark:text-amber-300">
                    Please check spelling or try a different skill name. Only skills from our database can be added.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
        <button 
          type="button"
          onClick={() => handleAdd()} 
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          disabled={!input.trim() || (hasSearched && suggestions.length === 0) || isSearching}
          title={hasSearched && suggestions.length === 0 ? "No matching skills found. Please select from suggestions." : "Add skill"}
        >
          Add
        </button>
      </div>
      
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
