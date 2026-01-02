'use client';

import Link from 'next/link';
import { KeywordDetail, KeywordHistory } from '@/lib/api';

interface KeywordDetailClientProps {
  keyword: KeywordDetail;
  history: KeywordHistory | null;
}

export default function KeywordDetailClient({ keyword, history }: KeywordDetailClientProps) {
  const snapshot = keyword.latest_snapshot;

  return (
    <div>
      <div className="mb-6">
        <Link
          href="/"
          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          ← Back to Home
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {keyword.keyword}
        </h1>
        {snapshot && (
          <div className="mt-4">
            <div className="flex items-center gap-6">
              <div>
                <div className="text-4xl font-bold text-blue-600">
                  {snapshot.momentum_score}
                </div>
                <div className="text-sm text-gray-500">Momentum Score</div>
              </div>
              <div className="text-sm text-gray-500">
                Last updated: {new Date(snapshot.snapshot_date).toLocaleDateString()}
              </div>
            </div>
          </div>
        )}
      </div>

      {snapshot && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Score Breakdown</h2>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Lift</span>
                  <span className="font-medium">{snapshot.lift_value.toFixed(2)}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${Math.min(100, Math.abs(snapshot.lift_value) * 10)}%` }}
                  ></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Acceleration</span>
                  <span className="font-medium">{snapshot.acceleration_value.toFixed(2)}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full"
                    style={{ width: `${Math.min(100, Math.abs(snapshot.acceleration_value) * 10)}%` }}
                  ></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Novelty</span>
                  <span className="font-medium">{(snapshot.novelty_value * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-purple-600 h-2 rounded-full"
                    style={{ width: `${snapshot.novelty_value * 100}%` }}
                  ></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Noise</span>
                  <span className="font-medium">{snapshot.noise_value.toFixed(2)}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-red-600 h-2 rounded-full"
                    style={{ width: `${Math.min(100, snapshot.noise_value * 10)}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Score Explanation</h2>
            <div className="space-y-3 text-sm text-gray-600">
              <p>
                <strong className="text-gray-900">Lift (45%):</strong> Compares recent 7 weeks to previous 21 weeks.
                Higher values indicate stronger growth.
              </p>
              <p>
                <strong className="text-gray-900">Acceleration (35%):</strong> Rate of change difference.
                Positive values show accelerating upward trends.
              </p>
              <p>
                <strong className="text-gray-900">Novelty (25%):</strong> Rewards historically low baselines.
                Higher values mean the keyword was previously less popular.
              </p>
              <p>
                <strong className="text-gray-900">Noise (-25%):</strong> Penalizes volatile spikes.
                Lower values indicate more stable growth.
              </p>
            </div>
          </div>
        </div>
      )}

      {history && history.history.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Score History</h2>
          <div className="space-y-2">
            {history.history.slice(0, 30).map((snapshot) => (
              <div
                key={snapshot.id}
                className="flex items-center justify-between p-3 border border-gray-200 rounded"
              >
                <div className="text-sm text-gray-600">
                  {new Date(snapshot.snapshot_date).toLocaleDateString()}
                </div>
                <div className="text-lg font-semibold text-blue-600">
                  {snapshot.momentum_score}
                </div>
              </div>
            ))}
            {history.history.length > 30 && (
              <p className="text-sm text-gray-500 text-center mt-4">
                Showing last 30 of {history.total} snapshots
              </p>
            )}
          </div>
        </div>
      )}

      {!snapshot && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800">
            No snapshot data available for this keyword yet.
          </p>
        </div>
      )}
    </div>
  );
}

