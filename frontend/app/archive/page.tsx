'use client';

import { useState, useEffect } from 'react';
import { api, ArchiveResponse, KeywordListItem } from '@/lib/api';
import KeywordList from '@/components/KeywordList';

export default function ArchivePage() {
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [archiveData, setArchiveData] = useState<ArchiveResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    // Load available dates
    api.getAvailableDates(30)
      .then(setAvailableDates)
      .catch((err) => {
        console.error('Error loading dates:', err);
        setError('Failed to load available dates');
      });
  }, []);

  useEffect(() => {
    if (selectedDate) {
      setIsLoading(true);
      setError(null);
      api.getArchive(selectedDate, page, 50)
        .then(setArchiveData)
        .catch((err) => {
          console.error('Error loading archive:', err);
          setError('Failed to load archive data');
          setArchiveData(null);
        })
        .finally(() => setIsLoading(false));
    }
  }, [selectedDate, page]);

  // Set default date to most recent
  useEffect(() => {
    if (availableDates.length > 0 && !selectedDate) {
      setSelectedDate(availableDates[0]);
    }
  }, [availableDates, selectedDate]);

  return (
    <main className="min-h-screen py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Archive</h1>
          <p className="text-lg text-gray-600">
            View historical keyword snapshots
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <label htmlFor="date-select" className="block text-sm font-medium text-gray-700 mb-2">
            Select Date
          </label>
          <select
            id="date-select"
            value={selectedDate}
            onChange={(e) => {
              setSelectedDate(e.target.value);
              setPage(1);
            }}
            className="block w-full max-w-xs rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          >
            {availableDates.map((date) => (
              <option key={date} value={date}>
                {new Date(date).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </option>
            ))}
          </select>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {archiveData && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="mb-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                Snapshot for {new Date(archiveData.date).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </h2>
              <p className="text-sm text-gray-500">
                {archiveData.total} keywords
              </p>
            </div>

            <KeywordList keywords={archiveData.keywords} isLoading={isLoading} />

            {archiveData.total > 0 && (
              <div className="mt-6 flex items-center justify-between">
                <div className="text-sm text-gray-500">
                  Showing {archiveData.keywords.length} of {archiveData.total} keywords
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={!archiveData.has_prev || isLoading}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage((p) => p + 1)}
                    disabled={!archiveData.has_next || isLoading}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}

