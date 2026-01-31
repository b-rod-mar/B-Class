import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { 
  Search, 
  Shield, 
  AlertTriangle,
  Loader2,
  Check
} from 'lucide-react';
import { cn } from '../lib/utils';

export default function HSCodeAutoSuggest({ 
  value, 
  onChange, 
  onSelect, 
  placeholder = "Search HS codes or descriptions...",
  className 
}) {
  const { api } = useAuth();
  const [query, setQuery] = useState(value || '');
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const wrapperRef = useRef(null);
  const inputRef = useRef(null);
  const debounceRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Sync external value
  useEffect(() => {
    if (value !== query) {
      setQuery(value || '');
    }
  }, [value]);

  // Debounced search
  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    if (!query || query.length < 2) {
      setSuggestions([]);
      setIsOpen(false);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const response = await api.get(`/hs-codes/suggest?q=${encodeURIComponent(query)}&limit=10`);
        setSuggestions(response.data.suggestions || []);
        setIsOpen(true);
        setSelectedIndex(-1);
      } catch (error) {
        console.error('HS code suggestion error:', error);
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [query, api]);

  const handleInputChange = (e) => {
    const newValue = e.target.value;
    setQuery(newValue);
    if (onChange) onChange(newValue);
  };

  const handleSelect = (suggestion) => {
    setQuery(suggestion.code);
    setIsOpen(false);
    if (onSelect) onSelect(suggestion);
    if (onChange) onChange(suggestion.code);
  };

  const handleKeyDown = (e) => {
    if (!isOpen || suggestions.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && suggestions[selectedIndex]) {
          handleSelect(suggestions[selectedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        break;
    }
  };

  return (
    <div ref={wrapperRef} className={cn("relative", className)}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          ref={inputRef}
          value={query}
          onChange={handleInputChange}
          onFocus={() => suggestions.length > 0 && setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="pl-9 pr-9 font-mono"
          data-testid="hs-autosuggest-input"
        />
        {loading && (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground" />
        )}
      </div>

      {/* Dropdown */}
      {isOpen && suggestions.length > 0 && (
        <div 
          className="absolute z-50 w-full mt-1 bg-card border border-border rounded-lg shadow-lg overflow-hidden"
          data-testid="hs-suggestions-dropdown"
        >
          <ul className="max-h-64 overflow-y-auto py-1">
            {suggestions.map((suggestion, idx) => (
              <li
                key={suggestion.code}
                onClick={() => handleSelect(suggestion)}
                className={cn(
                  "px-3 py-2 cursor-pointer transition-colors",
                  selectedIndex === idx 
                    ? "bg-primary/10" 
                    : "hover:bg-muted/50"
                )}
                data-testid={`hs-suggestion-${suggestion.code}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <code className="text-sm font-mono text-primary font-semibold">
                        {suggestion.code}
                      </code>
                      {suggestion.is_restricted && (
                        <Badge variant="outline" className="bg-rose-500/10 text-rose-400 border-rose-500/30 text-xs py-0">
                          <Shield className="h-3 w-3 mr-1" />
                          Restricted
                        </Badge>
                      )}
                      {suggestion.requires_permit && (
                        <Badge variant="outline" className="bg-amber-500/10 text-amber-400 border-amber-500/30 text-xs py-0">
                          <AlertTriangle className="h-3 w-3 mr-1" />
                          Permit
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground truncate mt-0.5">
                      {suggestion.description}
                    </p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <span className="text-xs text-muted-foreground">
                      Ch. {suggestion.chapter}
                    </span>
                    {suggestion.duty_rate && (
                      <p className="text-xs font-medium text-primary">
                        {suggestion.duty_rate}
                      </p>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* No results */}
      {isOpen && query.length >= 2 && !loading && suggestions.length === 0 && (
        <div className="absolute z-50 w-full mt-1 bg-card border border-border rounded-lg shadow-lg p-3">
          <p className="text-sm text-muted-foreground text-center">
            No matching HS codes found
          </p>
        </div>
      )}
    </div>
  );
}
