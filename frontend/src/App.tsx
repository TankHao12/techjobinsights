/**
 * Main App Component
 * Sets up routing, theme, and global layout
 */

import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Navigation } from './components/layout/Navigation';

// Page Imports
import Dashboard from './pages/Dashboard';
import SkillsAnalytics from './pages/Skills';
import SkillDetail from './pages/SkillDetail';
const SkillComparisonPage = React.lazy(() => import('./pages/SkillComparison'));
import Companies from './pages/Companies';
import CompanyDetail from './pages/CompanyDetail';
import About from './pages/About';

// Create React Query client
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 5 * 60 * 1000, // 5 minutes
            refetchOnWindowFocus: false,
            retry: 1,
        },
    },
});

/**
 * App Component
 * Main application wrapper
 */
function App() {
    const [theme, setTheme] = useState<'light' | 'dark'>('light');

    // Initialize theme from localStorage or system preference
    useEffect(() => {
        const savedTheme = localStorage.getItem('techinsights-theme') as 'light' | 'dark';
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

        const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');
        setTheme(initialTheme);

        if (initialTheme === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }, []);

    // Toggle theme
    const toggleTheme = () => {
        const newTheme = theme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);

        localStorage.setItem('techinsights-theme', newTheme);

        if (newTheme === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    };

    return (
        <QueryClientProvider client={queryClient}>
            <Router>
                <div className="min-h-screen flex flex-col bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-900 dark:to-black transition-colors duration-300">
                    <Navigation theme={theme} toggleTheme={toggleTheme} />

                    <main className="flex-grow container mx-auto px-4 py-8 max-w-7xl">
                        <Routes>
                            {/* Dashboard */}
                            <Route path="/" element={<Dashboard />} />

                            {/* Skills Routes */}
                            <Route path="/skills" element={<SkillsAnalytics />} />
                            <Route path="/skills/:skillName" element={<SkillDetail />} />
                            <Route
                                path="/skills/compare"
                                element={
                                    <React.Suspense fallback={<div>Loading...</div>}>
                                        <SkillComparisonPage />
                                    </React.Suspense>
                                }
                            />

                            {/* Companies Routes */}
                            <Route path="/companies" element={<Companies />} />
                            <Route path="/companies/:companyId" element={<CompanyDetail />} />

                            {/* About */}
                            <Route path="/about" element={<About />} />

                            {/* 404 - Not Found */}
                            <Route path="*" element={<NotFound />} />
                        </Routes>
                    </main>

                    {/* Footer */}
                    <footer className="mt-auto border-t border-gray-200 dark:border-gray-800 bg-gradient-to-r from-white/80 via-blue-50/50 to-purple-50/50 dark:from-gray-900/80 dark:via-gray-900/60 dark:to-gray-900/80 backdrop-blur-md">
                        <div className="container mx-auto px-4 py-6 max-w-7xl">
                            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                                <div className="text-center md:text-left">
                                    <p className="text-gray-800 dark:text-gray-200 font-semibold mb-1">NZ Tech Jobs Market Intelligence</p>
                                    <p className="text-sm text-gray-600 dark:text-gray-400">Data updated daily • Built for NZ tech professionals</p>
                                </div>
                                <div className="text-center md:text-right">
                                    <p className="text-sm text-gray-500 dark:text-gray-500">MVP v1.0 • © 2025</p>
                                    <p className="text-xs text-gray-400 dark:text-gray-600 mt-1">Empowering career decisions with data</p>
                                </div>
                            </div>
                        </div>
                    </footer>
                </div>
            </Router>
        </QueryClientProvider>
    );
}

/**
 * NotFound Component
 * 404 page
 */
const NotFound: React.FC = () => {
    return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
            <h1 className="text-6xl font-bold text-gray-300 dark:text-gray-700 mb-4">404</h1>
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-2">Page Not Found</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">The page you're looking for doesn't exist.</p>
            <a href="/" className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                Go to Dashboard
            </a>
        </div>
    );
};

export default App;
