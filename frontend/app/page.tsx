'use client';

import { useState, useEffect } from 'react';
import { api, KeywordListResponse } from '@/lib/api'
import KeywordList from '@/components/KeywordList'

export default function Home() {
  const [data, setData] = useState<KeywordListResponse>({
    items: [],
    total: 0,
    page: 1,
    page_size: 10,
    has_next: false,
    has_prev: false,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchKeywords() {
      try {
        setIsLoading(true);
        setError(null);
        // For free users, limit to top 10
        const result = await api.getKeywords(1, 10, 10);
        setData(result);
      } catch (err) {
        console.error('Error fetching keywords:', err);
        setError('Failed to load keywords');
      } finally {
        setIsLoading(false);
      }
    }

    fetchKeywords();
  }, []);

  return (
    <main className="min-h-screen py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            TikTok Keyword Momentum Tracker
          </h1>
          <p className="text-lg text-gray-600">
            Discover trending keywords before they peak
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="mb-6">
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">
              Top Trending Keywords
            </h2>
            <p className="text-sm text-gray-500">
              Ranked by momentum score (updated daily)
            </p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          <KeywordList keywords={data.items} isLoading={isLoading} />

          {data.items.length > 0 && !isLoading && (
            <div className="mt-6 text-center text-sm text-gray-500">
              Showing {data.items.length} of {data.total} keywords
            </div>
          )}
        </div>
      </div>
    </main>
  )
}

