/**
 * About Page
 * Information about the platform
 */

import React from 'react';
import { GlassCard } from '../components/common/GlassCard';
import { Target, TrendingUp, Database, Users } from 'lucide-react';

const About: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
          About NZ Tech Jobs Market Intelligence
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
          Your data-driven guide to the New Zealand technology job market
        </p>
      </div>

      {/* Mission */}
      <GlassCard>
        <div className="p-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            Our Mission
          </h2>
          <p className="text-gray-700 dark:text-gray-300 text-lg mb-4">
            We help tech professionals and job seekers make informed career decisions by providing
            comprehensive market intelligence on skill demand, technology trends, and company hiring
            patterns in New Zealand.
          </p>
          <p className="text-gray-700 dark:text-gray-300 text-lg">
            Rather than helping you search for jobs (that's what Seek and TradeMe are for), we help
            you understand the market so you can make strategic decisions about what skills to learn
            and which technologies to focus on.
          </p>
        </div>
      </GlassCard>

      {/* What We Do */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <GlassCard>
          <div className="p-6">
            <Target className="w-12 h-12 text-blue-600 mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Skills Analytics
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Track which technologies are most in-demand, identify emerging skills, and
              understand how skills pair together in real job postings.
            </p>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="p-6">
            <TrendingUp className="w-12 h-12 text-purple-600 mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Market Trends
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Monitor technology trends over time, spot growing and declining skills,
              and stay ahead of market shifts.
            </p>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="p-6">
            <Database className="w-12 h-12 text-green-600 mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Company Intelligence
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Discover what technologies companies use, understand their hiring patterns,
              and prepare yourself for opportunities.
            </p>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="p-6">
            <Users className="w-12 h-12 text-cyan-600 mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Career Guidance
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Compare different skills, understand salary ranges, and make data-driven
              decisions about your career path.
            </p>
          </div>
        </GlassCard>
      </div>

      {/* How It Works */}
      <GlassCard>
        <div className="p-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            How It Works
          </h2>
          <div className="space-y-4 text-gray-700 dark:text-gray-300">
            <div>
              <h3 className="font-semibold mb-2">1. Data Collection</h3>
              <p>
                We automatically scrape job postings from major NZ job boards daily, focusing
                specifically on technology roles.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">2. Skill Extraction</h3>
              <p>
                Using natural language processing, we extract skills, technologies, salary ranges,
                experience levels, and other key information from job descriptions.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">3. Data Analysis</h3>
              <p>
                We analyze patterns, calculate trends, identify skill combinations, and aggregate
                company tech stacks to provide meaningful insights.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">4. Visualization</h3>
              <p>
                The data is presented through interactive dashboards and visualizations that make
                it easy to understand market dynamics and make decisions.
              </p>
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Project Info */}
      <div className="text-center text-sm text-gray-500 dark:text-gray-400">
        <p>Built as part of COMP693 Industrial Project at Lincoln University</p>
      </div>
    </div>
  );
};

export default About;
