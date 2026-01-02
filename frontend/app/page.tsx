import { api, KeywordListResponse } from '@/lib/api'
import KeywordList from '@/components/KeywordList'

async function getKeywords(): Promise<KeywordListResponse> {
  try {
    // For free users, limit to top 10
    return await api.getKeywords(1, 10, 10)
  } catch (error) {
    console.error('Error fetching keywords:', error)
    return {
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
      has_next: false,
      has_prev: false,
    }
  }
}

export default async function Home() {
  const data = await getKeywords()

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

          <KeywordList keywords={data.items} />

          {data.items.length > 0 && (
            <div className="mt-6 text-center text-sm text-gray-500">
              Showing {data.items.length} of {data.total} keywords
            </div>
          )}
        </div>
      </div>
    </main>
  )
}

