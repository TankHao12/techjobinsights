/**
 * FilterDropdown Component
 * Custom dropdown for filtering data with full dark mode support
 * Uses Headless UI Listbox instead of native select for proper styling
 */

import React from 'react';
import { Listbox } from '@headlessui/react';
import { ChevronDown, Check } from 'lucide-react';

export interface FilterOption {
  value: string | number;
  label: string;
}

export interface FilterDropdownProps {
  label: string;
  value: string | number;
  options: FilterOption[];
  onChange: (value: string | number) => void;
  className?: string;
}

const FilterDropdown: React.FC<FilterDropdownProps> = ({
  label,
  value,
  options,
  onChange,
  className = '',
}) => {
  const selectedOption = options.find(opt => opt.value === value);

  return (
    <div className={`inline-flex items-center gap-2 ${className}`}>
      <label className="text-sm font-medium text-gray-600 dark:text-gray-400 whitespace-nowrap">
        {label}
      </label>
      <Listbox value={value} onChange={onChange}>
        <div className="relative">
          <Listbox.Button className="relative appearance-none w-full text-left pl-4 pr-10 py-2.5 min-w-[140px] bg-white dark:bg-gray-800 backdrop-blur-sm border border-gray-200 dark:border-gray-700 rounded-xl text-sm font-semibold text-gray-900 dark:text-gray-100 shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all duration-200 cursor-pointer">
            <span className="block truncate">{selectedOption?.label}</span>
            <span className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
              <ChevronDown className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            </span>
          </Listbox.Button>

          <Listbox.Options className="absolute z-10 mt-1 w-full max-h-60 overflow-auto rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-lg py-1 focus:outline-none">
            {options.map((option) => (
              <Listbox.Option
                key={option.value}
                value={option.value}
                className={({ active }) => `relative cursor-pointer select-none py-2 pl-4 pr-10 ${active ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-900 dark:text-blue-100' : 'text-gray-900 dark:text-gray-100'} transition-colors duration-150`}
              >
                {({ selected }) => (
                  <>
                    <span className="block truncate text-sm font-medium">
                      {option.label}
                    </span>
                    {selected && (
                      <span className="absolute inset-y-0 right-0 flex items-center pr-3 text-blue-600 dark:text-blue-400">
                        <Check className="w-4 h-4" />
                      </span>
                    )}
                  </>
                )}
              </Listbox.Option>
            ))}
          </Listbox.Options>
        </div>
      </Listbox>
    </div>
  );
};

export default FilterDropdown;


