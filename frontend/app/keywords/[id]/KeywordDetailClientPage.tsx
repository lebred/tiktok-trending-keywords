'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api, KeywordDetail, KeywordHistory } from '@/lib/api';
import KeywordDetailClient from '@/components/KeywordDetailClient';

export default function KeywordDetailClientPage({ id }: { id: number }) {
  const router = useRouter();
  const [keyword, setKeyword] = useState<KeywordDetail | null>(null);
  const [history, setHistory] = useState<KeywordHistory | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!Number.isFinite(id) || id <= 0) {
      setError('Invalid keyword ID');
      setIsLoading(false);
      return;
    }

    async function fetchData() {
      try {
        setIsLoading(true);
        setError(null);

        const [keywordData, historyData] = await Promise.all([
          api.getKeyword(id),
          api.getKeywordHistory(id, 90).catch(() => null),
        ]);

        setKeyword(keywordData);
        setHistory(historyData);
      } catch (err) {
        console.error('Error fetching keyword data:', err);
        setError('Failed to load keyword data');
      } finally {
        setIsLoading(false);
      }
    }

    fetchData();
  }, [id]);

  if (isLoading) {
    return (
      <main className="min-h-screen py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </div>
      </main>
    );
  }

  if (error || !keyword) {
    return (
      <main className="min-h-screen py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">{error || 'Keyword not found'}</p>
            <button
              onClick={() => router.push('/')}
              className="mt-4 text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              ← Back to Home
            </button>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <KeywordDetailClient keyword={keyword} history={history} />
      </div>
    </main>
  );
}

