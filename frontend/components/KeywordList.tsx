/**
 * Keyword list component.
 */

'use client';

import Link from 'next/link';
import { KeywordListItem } from '@/lib/api';

interface KeywordListProps {
  keywords: KeywordListItem[];
  isLoading?: boolean;
}

export default function KeywordList({ keywords, isLoading }: KeywordListProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(10)].map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="h-16 bg-gray-200 rounded-lg"></div>
          </div>
        ))}
      </div>
    );
  }

  if (keywords.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No keywords found.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {keywords.map((keyword) => (
        <Link
          key={keyword.id}
          href={`/keywords/${keyword.id}`}
          className="block bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow p-6 border border-gray-200"
        >
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900">
                {keyword.keyword}
              </h3>
              {keyword.snapshot_date && (
                <p className="text-sm text-gray-500 mt-1">
                  Updated: {new Date(keyword.snapshot_date).toLocaleDateString()}
                </p>
              )}
            </div>
            {keyword.momentum_score !== null && (
              <div className="ml-4">
                <div className="text-right">
                  <div className="text-2xl font-bold text-blue-600">
                    {keyword.momentum_score}
                  </div>
                  <div className="text-xs text-gray-500">Momentum</div>
                </div>
              </div>
            )}
          </div>
        </Link>
      ))}
    </div>
  );
}

